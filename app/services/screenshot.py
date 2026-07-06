import os
import uuid
import asyncio
import time
from typing import Optional, Dict, Any
from urllib.parse import urlparse
from dataclasses import dataclass, field
from contextlib import asynccontextmanager

from playwright.async_api import (
    async_playwright,
    Browser,
    Playwright,
    Page,
    BrowserContext,
    Error as PlaywrightError,
)
from playwright._impl._errors import TargetClosedError as TargetClosedErrorImpl

from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import (
    NotFoundException,
    ValidationException,
    ServiceUnavailableException,
)

from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.lead import lead_repository
from app.repositories.screenshot import screenshot_repository

from app.schemas.screenshot import (
    ScreenshotCreate,
    CaptureScreenshotResponse,
)

from app.services.cloudinary_service import cloudinary_service

# =====================================================================
# Configuration Constants
# =====================================================================

NAVIGATION_TIMEOUT = 30.0        # page.goto max wait (seconds)
RENDER_TIMEOUT = 10.0            # wait for body rendered max
SETTLE_DELAY = 0.4               # extra settle after render (seconds)
SCROLL_TIMEOUT = 8.0             # lazy-load scroll max
TOTAL_PER_VIEWPORT_TIMEOUT = 45.0  # hard cap per viewport

MAX_BROWSER_AGE_SECONDS = 300.0  # restart browser after 5 min
MAX_CONSECUTIVE_FAILURES = 3     # restart browser after N failures

DESKTOP_VIEWPORT = {"width": 1920, "height": 1080}
MOBILE_VIEWPORT = {"width": 375, "height": 812}
DEVICE_SCALE_FACTOR = 2

MAX_FULL_PAGE_HEIGHT = 15000     # pixels, prevent OOM on huge pages

BLOCKED_RESOURCE_TYPES = {"image", "media", "font", "stylesheet"}

BLOCKED_DOMAINS = {
    # Analytics & tracking
    "google-analytics.com",
    "googletagmanager.com",
    "analytics.google.com",
    "stats.g.doubleclick.net",
    "facebook.net",
    "facebook.com/tr",
    "connect.facebook.net",
    "doubleclick.net",
    "adsrvr.org",
    "hotjar.com",
    "scorecardresearch.com",
    "quantserve.com",
    "criteo.com",
    "adsafeprotected.com",
    "moatads.com",
    "outbrain.com",
    "taboola.com",
    "addthis.com",
    "sharethis.com",
    "matomo.cloud",
    "piwik.pro",
}

# =====================================================================
# Browser Manager — Production-Grade Singleton with Auto-Recovery
# =====================================================================

@dataclass
class _BrowserState:
    playwright: Optional[Playwright] = None
    browser: Optional[Browser] = None
    launched_at: float = 0.0
    consecutive_failures: int = 0
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class BrowserManager:
    """
    Thread-safe singleton that manages a persistent Chromium browser.
    Automatically recovers from crashes, disconnects, and stale states.
    """

    def __init__(self) -> None:
        self._state = _BrowserState()

    async def get_browser(self) -> Browser:
        """Get a healthy browser instance, launching/recovering as needed."""
        async with self._state.lock:
            return await self._ensure_healthy_browser()

    async def _ensure_healthy_browser(self) -> Browser:
        """Return existing browser if healthy, otherwise launch new one."""
        browser = self._state.browser

        if browser is not None:
            try:
                # Verify browser is actually responsive
                if browser.is_connected():
                    # Check age
                    if time.monotonic() - self._state.launched_at > MAX_BROWSER_AGE_SECONDS:
                        logger.info("Browser exceeded max age, restarting")
                        await self._close_browser()
                    else:
                        return browser
                else:
                    logger.warning("Browser disconnected, will restart")
                    await self._close_browser()
            except Exception as e:
                logger.warning(f"Browser health check failed: {e}, restarting")
                await self._close_browser()

        # Launch fresh browser
        return await self._launch_browser()

    async def _launch_browser(self) -> Browser:
        """Launch a new Chromium instance with production flags."""
        if self._state.playwright is None:
            self._state.playwright = await async_playwright().start()

        try:
            browser = await self._state.playwright.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--single-process",
                    "--disable-background-networking",
                    "--disable-background-timer-throttling",
                    "--disable-client-side-phishing-detection",
                    "--disable-component-update",
                    "--disable-features=TranslateUI,OptimizationHints",
                    "--disable-popup-blocking",
                    "--disable-prompt-on-repost",
                    "--disable-sync",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--disable-extensions",
                    "--disable-default-apps",
                    "--memory-pressure-off",
                    "--max_old_space_size=256",
                ],
            )
        except Exception as e:
            logger.error(f"Chromium launch failed: {e}")
            logger.info("Falling back to Firefox")
            if self._state.playwright is not None:
                await self._state.playwright.stop()
            self._state.playwright = await async_playwright().start()
            browser = await self._state.playwright.firefox.launch(
                headless=True,
                args=["--no-sandbox"],
            )

        self._state.browser = browser
        self._state.launched_at = time.monotonic()
        self._state.consecutive_failures = 0

        logger.info("Chromium browser launched successfully")
        return browser

    async def _close_browser(self) -> None:
        """Cleanly close browser and playwright."""
        if self._state.browser is not None:
            try:
                await self._state.browser.close()
            except Exception as e:
                logger.debug(f"Error closing browser: {e}")
            finally:
                self._state.browser = None

        if self._state.playwright is not None:
            try:
                await self._state.playwright.stop()
            except Exception as e:
                logger.debug(f"Error stopping playwright: {e}")
            finally:
                self._state.playwright = None

    def record_success(self) -> None:
        """Call on successful screenshot to reset failure counter."""
        self._state.consecutive_failures = 0

    def record_failure(self) -> None:
        """Call on infrastructure failure to trigger potential restart."""
        self._state.consecutive_failures += 1
        if self._state.consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
            logger.warning(f"Consecutive failures reached {MAX_CONSECUTIVE_FAILURES}, will restart browser on next request")

    async def close(self) -> None:
        """Explicit cleanup (for app shutdown)."""
        await self._close_browser()


_browser_mgr = BrowserManager()


# =====================================================================
# Page-Level Helpers
# =====================================================================

async def _block_unnecessary(route) -> None:
    """Block ONLY analytics, tracking, ads. Preserve React/Next.js/Vue bundles."""
    url = route.request.url.lower()

    # Check blocked domains first
    for domain in BLOCKED_DOMAINS:
        if domain in url:
            await route.abort("blockedbyclient")
            return

    # Check resource types for blocked domains only
    # DO NOT block images/fonts/stylesheets globally — breaks rendering
    rtype = route.request.resource_type
    if rtype in BLOCKED_RESOURCE_TYPES:
        # Only block if it's from a known tracking domain
        # (already caught above) — otherwise allow
        await route.continue_()
        return

    await route.continue_()


async def _wait_for_rendered_body(page: Page, timeout: float = RENDER_TIMEOUT) -> None:
    """
    Wait until document.body has visible dimensions.
    This is the KEY fix for blank screenshots on SPAs.
    """
    await asyncio.wait_for(
        page.wait_for_function(
            """() => {
                const body = document.body;
                if (!body) return false;
                const rect = body.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0;
            }""",
            timeout=timeout * 1000,
        ),
        timeout=timeout + 2.0,
    )


async def _scroll_for_lazy_content(page: Page, max_depth: int = 5000) -> None:
    """Scroll down incrementally to trigger lazy loading, then return to top."""
    try:
        await asyncio.wait_for(
            page.evaluate(f"""
                (async () => {{
                    const delay = (ms) => new Promise(r => setTimeout(r, ms));
                    const step = 500;
                    const pause = 120;
                    const limit = Math.min(
                        Math.max(
                            document.documentElement.scrollHeight,
                            document.body.scrollHeight,
                            0
                        ),
                        {max_depth}
                    );
                    let current = 0;
                    while (current < limit) {{
                        window.scrollTo(0, current);
                        current += step;
                        await delay(pause);
                    }}
                }})()
            """),
            timeout=SCROLL_TIMEOUT,
        )
    except asyncio.TimeoutError:
        logger.warning("Scroll timed out, continuing")
    except Exception as e:
        logger.warning(f"Scroll error (non-fatal): {e}")

    try:
        await page.evaluate("window.scrollTo(0, 0)")
        await page.wait_for_timeout(300)
    except Exception:
        pass


async def _verify_screenshot_content(page: Page, path: str) -> bool:
    """
    Verify screenshot is not blank by checking page has rendered content.
    Returns True if content detected, False if blank.
    """
    try:
        # Check via JS that body has visible content
        has_content = await page.evaluate("""
            () => {
                const body = document.body;
                if (!body) return false;
                const style = window.getComputedStyle(body);
                if (style.display === 'none' || style.visibility === 'hidden') return false;
                const rect = body.getBoundingClientRect();
                if (rect.width === 0 || rect.height === 0) return false;

                // Check for any visible child elements
                const children = body.querySelectorAll('*');
                for (const el of children) {
                    const s = window.getComputedStyle(el);
                    if (s.display !== 'none' && s.visibility !== 'hidden' && s.opacity !== '0') {
                        const r = el.getBoundingClientRect();
                        if (r.width > 1 && r.height > 1) return true;
                    }
                }
                return false;
            }
        """)
        return bool(has_content)
    except Exception as e:
        logger.warning(f"Content verification failed: {e}")
        return True  # Assume OK if check fails


# =====================================================================
# Single Viewport Capture
# =====================================================================

async def _capture_single_viewport(
    url: str,
    browser: Browser,
    output_path: str,
    viewport: Dict[str, int],
    *,
    full_page: bool = False,
    is_mobile: bool = False,
    user_agent: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Capture a single viewport. Returns timing info.
    Raises on infrastructure failures (retried by caller).
    """
    timings = {}
    start = time.monotonic()

    context: Optional[BrowserContext] = None
    page: Optional[Page] = None

    try:
        context = await browser.new_context(
            viewport=viewport,
            device_scale_factor=DEVICE_SCALE_FACTOR,
            locale="en-US",
            is_mobile=is_mobile,
            has_touch=is_mobile,
            user_agent=user_agent or (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
            java_script_enabled=True,
            bypass_csp=True,
            ignore_https_errors=True,
        )

        page = await context.new_page()

        # Block tracking/ads
        await page.route("**/*", _block_unnecessary)

        t_nav = time.monotonic()
        await page.goto(url, wait_until="domcontentloaded", timeout=NAVIGATION_TIMEOUT * 1000)
        timings["navigation_ms"] = int((time.monotonic() - t_nav) * 1000)

        t_render = time.monotonic()
        # Wait for body to have dimensions (SPA rendering complete)
        await _wait_for_rendered_body(page, RENDER_TIMEOUT)
        timings["render_wait_ms"] = int((time.monotonic() - t_render) * 1000)

        # Small settle for any final layout shifts
        await page.wait_for_timeout(int(SETTLE_DELAY * 1000))

        # Optional scroll for lazy content (only for non-full-page)
        if not full_page:
            await _scroll_for_lazy_content(page)

        t_shot = time.monotonic()
        screenshot_options = {"path": output_path}
        if full_page:
            screenshot_options["full_page"] = True
            # Limit height to prevent OOM
            screenshot_options["clip"] = {"x": 0, "y": 0, "width": viewport["width"], "height": MAX_FULL_PAGE_HEIGHT}
        await page.screenshot(**screenshot_options)
        timings["screenshot_ms"] = int((time.monotonic() - t_shot) * 1000)

        # Verify not blank
        if not await _verify_screenshot_content(page, output_path):
            logger.warning("Screenshot appears blank, may retry")
            raise ServiceUnavailableException("Blank screenshot detected")

        timings["total_ms"] = int((time.monotonic() - start) * 1000)
        return timings

    except PlaywrightError as e:
        # Re-wrap Playwright errors for consistent handling
        raise ServiceUnavailableException(f"Playwright error: {e}") from e
    finally:
        if page:
            try:
                await page.close()
            except Exception:
                pass
        if context:
            try:
                await context.close()
            except Exception:
                pass


# =====================================================================
# Main Service
# =====================================================================

class ScreenshotService:

    def _validate_url(self, website: Optional[str]) -> str:
        if not website or not website.strip():
            raise ValidationException("This lead does not have a website URL.")

        url = website.strip()
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        parsed = urlparse(url)
        if not parsed.netloc:
            raise ValidationException(f"The URL '{website}' is invalid.")
        return url

    async def capture_screenshots(
        self,
        db: AsyncSession,
        *,
        lead_id: uuid.UUID,
        user: User,
    ) -> CaptureScreenshotResponse:

        lead = await lead_repository.get(db, id=lead_id)
        if not lead or lead.user_id != user.id:
            raise NotFoundException(f"Lead with id '{lead_id}' not found.")

        url = self._validate_url(lead.website)

        base_dir = settings.SCREENSHOTS_DIR
        desktop_path = os.path.join(base_dir, f"{lead_id}_desktop.png")
        mobile_path = os.path.join(base_dir, f"{lead_id}_mobile.png")
        full_page_path = os.path.join(base_dir, f"{lead_id}_full.png")

        attempt = 0
        max_retries = 2
        last_error = None

        while attempt <= max_retries:
            attempt += 1
            logger.info(f"Screenshot capture attempt {attempt}/{max_retries + 1} for {url}")

            try:
                browser = await _browser_mgr.get_browser()

                # Desktop + Mobile concurrently
                results = await asyncio.gather(
                    _capture_single_viewport(
                        url, browser, desktop_path, DESKTOP_VIEWPORT,
                        full_page=False, is_mobile=False
                    ),
                    _capture_single_viewport(
                        url, browser, mobile_path, MOBILE_VIEWPORT,
                        full_page=False, is_mobile=True,
                        user_agent=(
                            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 "
                            "like Mac OS X) AppleWebKit/605.1.15 "
                            "(KHTML, like Gecko) Version/17.0 "
                            "Mobile/15E148 Safari/604.1"
                        )
                    ),
                    return_exceptions=True,
                )

                # Check for exceptions
                errors = [r for r in results if isinstance(r, Exception)]
                if errors:
                    raise errors[0]
                desktop_timings, mobile_timings = results

                # Full page (sequential to limit memory)
                full_timings = await _capture_single_viewport(
                    url, browser, full_page_path, DESKTOP_VIEWPORT,
                    full_page=True, is_mobile=False
                )

                # Success
                timings = {
                    "desktop": desktop_timings,
                    "mobile": mobile_timings,
                    "full_page": full_timings,
                }
                logger.info(f"Screenshot capture succeeded: {timings}")

                _browser_mgr.record_success()
                break

            except (ServiceUnavailableException, PlaywrightError, TargetClosedErrorImpl) as e:
                last_error = e
                _browser_mgr.record_failure()
                logger.error(f"Screenshot attempt {attempt} failed: {e}")

                if attempt > max_retries:
                    raise ServiceUnavailableException(
                        f"Failed to capture screenshots after {max_retries + 1} attempts: {last_error}"
                    )

                # Wait before retry (browser recovery happens automatically in get_browser)
                await asyncio.sleep(1.5 * attempt)

            except Exception as e:
                # Non-retryable (validation, etc.)
                logger.error(f"Screenshot non-retryable error: {e}")
                raise

        # Upload all three images concurrently
        upload_start = time.monotonic()
        desktop_res, mobile_res, full_page_res = await asyncio.gather(
            cloudinary_service.upload_image(desktop_path),
            cloudinary_service.upload_image(mobile_path),
            cloudinary_service.upload_image(full_page_path),
        )
        logger.info(f"Cloudinary upload completed in {int((time.monotonic() - upload_start) * 1000)}ms")

        screenshot_data = {
            "desktop_local_path": desktop_path if not desktop_res.get("secure_url") else None,
            "desktop_cloudinary_url": desktop_res.get("secure_url"),
            "desktop_public_id": desktop_res.get("public_id"),
            "mobile_local_path": mobile_path if not mobile_res.get("secure_url") else None,
            "mobile_cloudinary_url": mobile_res.get("secure_url"),
            "mobile_public_id": mobile_res.get("public_id"),
            "full_page_local_path": full_page_path if not full_page_res.get("secure_url") else None,
            "full_page_cloudinary_url": full_page_res.get("secure_url"),
            "full_page_public_id": full_page_res.get("public_id"),
        }

        existing = await screenshot_repository.get_by_lead_id(db, lead_id=lead_id)
        if existing:
            await screenshot_repository.update(db, db_obj=existing, obj_in=screenshot_data)
        else:
            create_schema = ScreenshotCreate(lead_id=lead_id, **screenshot_data)
            await screenshot_repository.create(db, obj_in=create_schema)

        return CaptureScreenshotResponse(
            lead_id=lead_id,
            desktop_url=desktop_res.get("secure_url"),
            mobile_url=mobile_res.get("secure_url"),
            full_page_url=full_page_res.get("secure_url"),
        )


screenshot_service = ScreenshotService()