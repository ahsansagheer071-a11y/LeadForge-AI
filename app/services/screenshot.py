import os
import uuid
import asyncio
from typing import Optional
from urllib.parse import urlparse
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import NotFoundException, ValidationException, ServiceUnavailableException
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.lead import lead_repository
from app.repositories.screenshot import screenshot_repository
from app.schemas.screenshot import ScreenshotCreate, CaptureScreenshotResponse
from app.services.cloudinary_service import cloudinary_service


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

    async def capture_screenshots(self, db: AsyncSession, *, lead_id: uuid.UUID, user: User) -> CaptureScreenshotResponse:
        lead = await lead_repository.get(db, id=lead_id)
        if not lead or lead.user_id != user.id:
            raise NotFoundException(f"Lead with id '{lead_id}' not found.")

        url = self._validate_url(lead.website)
        
        # Define paths
        base_dir = settings.SCREENSHOTS_DIR
        desktop_path = os.path.join(base_dir, f"{lead_id}_desktop.png")
        mobile_path = os.path.join(base_dir, f"{lead_id}_mobile.png")
        full_page_path = os.path.join(base_dir, f"{lead_id}_full.png")

        # Capture logic with retry
        max_retries = 1
        attempt = 0
        success = False

        while attempt <= max_retries and not success:
            try:
                await self._run_playwright(url, desktop_path, mobile_path, full_page_path)
                success = True
            except Exception as e:
                attempt += 1
                logger.error("Playwright capture failed for %s. Attempt %d. Error: %s", url, attempt, e)
                if attempt > max_retries:
                    raise ServiceUnavailableException(f"Failed to capture screenshots for {url}: {e}")
                await asyncio.sleep(2)

        # Upload to Cloudinary
        desktop_res = await cloudinary_service.upload_image(desktop_path)
        mobile_res = await cloudinary_service.upload_image(mobile_path)
        full_page_res = await cloudinary_service.upload_image(full_page_path)

        # Build DB update object
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

        # Update or Create DB record
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
            full_page_url=full_page_res.get("secure_url")
        )

    async def _run_playwright(self, url: str, desktop_path: str, mobile_path: str, full_page_path: str):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                # Desktop & Full Page
                desktop_context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
                page = await desktop_context.new_page()
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await page.screenshot(path=desktop_path)
                await page.screenshot(path=full_page_path, full_page=True)
                await desktop_context.close()

                # Mobile
                mobile_context = await browser.new_context(
                    viewport={'width': 375, 'height': 812},
                    is_mobile=True,
                    has_touch=True,
                    user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
                )
                mobile_page = await mobile_context.new_page()
                await mobile_page.goto(url, wait_until="networkidle", timeout=30000)
                await mobile_page.screenshot(path=mobile_path)
                await mobile_context.close()
            finally:
                await browser.close()


screenshot_service = ScreenshotService()
