"""
Patch script: replaces build_profile in service.py with the fixed version.
Run from the project root with:
    python patch_build_profile.py
"""
import re, pathlib, sys, textwrap

TARGET = pathlib.Path("app/services/website_intelligence/service.py")

# ── Exact start/end markers ──────────────────────────────────────────
START_MARKER = "    async def build_profile(\n"
END_MARKER   = "    async def validate_profile("

NEW_METHOD = textwrap.dedent('''\
    async def build_profile(
        self,
        db: AsyncSession,
        *,
        lead: Lead,
        url: str,
    ) -> Optional[WebsiteProfile]:
        """
        Extract a comprehensive WebsiteProfile from a lead's website.

        Uses Playwright (headless) to render the full page, then parses the
        DOM with BeautifulSoup to extract business info, design tokens,
        content sections, SEO metadata, and more.

        Crawl is done with domcontentloaded (not networkidle) so complex
        sites with infinite network activity don't time out.  All heavy
        resources (video/audio/tracking) are blocked.  Every page-level
        extraction runs BEFORE the browser context is closed.  A failed
        sub-extraction is non-fatal: the profile is built with whatever
        data is available.

        Returns None only if the page failed completely and produced no HTML.
        """
        import asyncio as _asyncio, time as _time
        crawl_start = _time.monotonic()
        logger.info(
            "build_profile started | lead_id=%s | url=%s",
            lead.id, url,
        )

        # ── Resource blocklist ──────────────────────────────────────── #
        _BLOCKED_CRAWL_TYPES = frozenset({"media", "video", "audio"})
        _BLOCKED_CRAWL_DOMAINS = frozenset({
            "google-analytics.com", "googletagmanager.com",
            "analytics.google.com", "facebook.net",
            "connect.facebook.net", "doubleclick.net",
            "hotjar.com", "scorecardresearch.com",
            "criteo.com", "taboola.com", "outbrain.com",
            "addthis.com", "matomo.cloud", "piwik.pro",
        })

        async def _block_crawl(route):
            try:
                rtype = route.request.resource_type
                rurl  = route.request.url.lower()
                if rtype in _BLOCKED_CRAWL_TYPES:
                    await route.abort("blockedbyclient")
                    return
                for dom in _BLOCKED_CRAWL_DOMAINS:
                    if dom in rurl:
                        await route.abort("blockedbyclient")
                        return
                await route.continue_()
            except Exception:
                try:
                    await route.continue_()
                except Exception:
                    pass

        # Accumulated crawl outputs
        html:                  Optional[str]        = None
        computed:              dict                 = {}
        color_palette                               = None
        logo_info_val                               = None
        typography_info_val                         = None
        consistency_report_val                      = None
        component_styles_val                        = None
        navigation_info_val                         = None
        hero_info_val                               = None
        hero_selector:         Optional[str]        = None
        crawl_timed_out                             = False
        crawl_blocked                               = False

        browser = await _browser_mgr.get_browser()
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
            bypass_csp=True,
            ignore_https_errors=True,
        )
        page = await context.new_page()

        try:
            await page.route("**/*", _block_crawl)

            # ── Phase 1: Navigation (domcontentloaded, 25 s) ────────── #
            try:
                logger.info(
                    "build_profile: navigating (domcontentloaded, 25 s) | url=%s", url
                )
                await page.goto(url, wait_until="domcontentloaded", timeout=25000)
                logger.info(
                    "build_profile: navigation OK | %.1f s",
                    _time.monotonic() - crawl_start,
                )
            except Exception as nav_exc:
                exc_name = type(nav_exc).__name__
                msg = str(nav_exc).lower()
                logger.warning(
                    "build_profile: navigation issue (%s: %s) — attempting partial capture",
                    exc_name, str(nav_exc)[:200],
                )
                if "net::" in msg or "err_name_not_resolved" in msg or "err_connection_refused" in msg:
                    crawl_blocked = True
                else:
                    crawl_timed_out = True
                # Do NOT raise — try to capture whatever the page loaded

            # ── Phase 2: Optional settle (3 s networkidle, non-fatal) ─ #
            try:
                await _asyncio.wait_for(
                    page.wait_for_load_state("networkidle"),
                    timeout=3.0,
                )
            except Exception:
                pass

            # Optional font-ready wait (2 s max)
            try:
                await page.wait_for_function(
                    "() => document.fonts.ready.then(() => true)",
                    timeout=2000,
                )
            except Exception:
                pass

            # Incremental scroll to trigger lazy-loading (max 5 steps)
            try:
                prev_height = 0
                for _ in range(5):
                    current = await page.evaluate("document.body.scrollHeight")
                    if current == prev_height:
                        break
                    prev_height = current
                    await page.evaluate(f"window.scrollTo(0, {current})")
                    await page.wait_for_timeout(150)
                await page.evaluate("window.scrollTo(0, 0)")
                await page.wait_for_timeout(200)
            except Exception:
                pass

            # ── Phase 3: Capture HTML ──────────────────────────────── #
            try:
                html = await page.content()
                logger.info(
                    "build_profile: HTML captured | %d bytes | %.1f s elapsed",
                    len(html.encode("utf-8")) if html else 0,
                    _time.monotonic() - crawl_start,
                )
            except Exception as html_exc:
                logger.warning("build_profile: HTML capture failed (%s)", html_exc)

            # ── Phase 4: Computed styles ───────────────────────────── #
            try:
                computed = await page.evaluate("""() => {
                    const body = document.body;
                    const h1 = document.querySelector('h1');
                    const h2 = document.querySelector('h2');
                    const h3 = document.querySelector('h3');
                    const h1Style = h1 ? getComputedStyle(h1) : null;
                    const h2Style = h2 ? getComputedStyle(h2) : null;
                    const h3Style = h3 ? getComputedStyle(h3) : null;
                    const bodyStyle = getComputedStyle(body);
                    const allFonts = new Set();
                    const walker = document.createTreeWalker(body, NodeFilter.SHOW_ELEMENT);
                    while (walker.nextNode()) {
                        const el = walker.currentNode;
                        const f = getComputedStyle(el).fontFamily;
                        if (f) f.split(',').forEach(x => {
                            const t = x.replace(/['"]/g, '').trim();
                            if (t && t !== 'serif' && t !== 'sans-serif' && t !== 'monospace') allFonts.add(t);
                        });
                    }
                    return {
                        bodyFont: bodyStyle.fontFamily,
                        h1Font: h1Style ? h1Style.fontFamily : null,
                        h2Font: h2Style ? h2Style.fontFamily : null,
                        h3Font: h3Style ? h3Style.fontFamily : null,
                        detectedFonts: Array.from(allFonts),
                    };
                }""")
            except Exception as ce:
                logger.warning("build_profile: computed styles failed (%s)", ce)
                computed = {}

            # ── Phase 5: Colour palette ────────────────────────────── #
            try:
                color_palette = await self.extract_color_palette(page)
            except Exception as cpe:
                logger.warning("build_profile: color palette failed (%s)", cpe)

            # ── Phase 6: Page-dependent extractions (all non-fatal) ── #
            if html:
                try:
                    logo_info_val = await self.extract_logo_info(page, html, url)
                except Exception as e:
                    logger.warning("build_profile: logo_info failed (%s)", e)

                try:
                    typography_info_val = await self.extract_typography(page, html)
                except Exception as e:
                    logger.warning("build_profile: typography failed (%s)", e)

                try:
                    consistency_report_val = await self.analyze_visual_consistency(page, None)
                except Exception as e:
                    logger.warning("build_profile: consistency_report failed (%s)", e)

                try:
                    component_styles_val = await self.extract_component_styles(page, html)
                except Exception as e:
                    logger.warning("build_profile: component_styles failed (%s)", e)

                try:
                    navigation_info_val = await self.extract_navigation(page, html)
                except Exception as e:
                    logger.warning("build_profile: navigation_info failed (%s)", e)

                try:
                    hero_info_val = await self.extract_hero_section(page, html)
                except Exception as e:
                    logger.warning("build_profile: hero_info failed (%s)", e)

                try:
                    hero_selector = await page.evaluate("""() => {
                        const el = document.querySelector('[class*="hero"], [id*="hero"]');
                        if (!el) {
                            const fallback = document.querySelector('section');
                            if (fallback) return 'section';
                            return null;
                        }
                        if (el.id) return '#' + CSS.escape(el.id);
                        const cls = Array.from(el.classList).find(c => c.toLowerCase().includes('hero'));
                        if (cls) return '[class*="' + CSS.escape(cls) + '"]';
                        return el.tagName.toLowerCase();
                    }""")
                except Exception:
                    pass

        except Exception as exc:
            logger.error(
                "build_profile: unexpected failure | url=%s | %s: %s",
                url, type(exc).__name__, exc,
            )
        finally:
            # Always close the browser context
            try:
                await context.close()
            except Exception:
                pass

        crawl_duration = _time.monotonic() - crawl_start
        logger.info(
            "build_profile: crawl finished | lead_id=%s | %.1f s | "
            "html=%s | timed_out=%s | blocked=%s",
            lead.id, crawl_duration,
            f"{len(html.encode('utf-8')) // 1024}KB" if html else "None",
            crawl_timed_out, crawl_blocked,
        )

        if not html:
            logger.warning(
                "build_profile: no HTML captured | url=%s — cannot build profile", url
            )
            return None

        # ── Post-crawl: DOM parsing (no live browser needed) ─────────── #
        soup = BeautifulSoup(html, "html.parser")
        raw_size_kb = round(len(html.encode("utf-8")) / 1024, 2)

        # Truncate huge HTML to avoid memory spikes in BeautifulSoup
        if raw_size_kb > 2048:
            logger.warning(
                "build_profile: HTML too large (%.0f KB) — truncating to 2 MB", raw_size_kb,
            )
            html = html[:2_097_152]
            soup = BeautifulSoup(html, "html.parser")

        from app.services.website_intelligence.schemas import ColorPalette as _CP
        if color_palette is None:
            color_palette = _CP()

        brand = self._extract_brand_identity(
            soup, computed, color_palette,
            logo_info_val, typography_info_val,
        )
        if consistency_report_val is not None:
            brand.consistency_report = consistency_report_val
        if component_styles_val is not None:
            brand.component_styles = component_styles_val

        brand.design_language    = self.classify_design_language(brand, html)
        brand.brand_personality  = self.estimate_brand_personality(brand, html)

        sections = self.extract_sections(html, hero_selector)
        ctas     = self.extract_ctas(html, sections, hero_info_val)
        footer_nav_items = navigation_info_val.footer_nav_items if navigation_info_val else []

        # Remaining extractions are HTML-only (pass page=None safely)
        try:
            footer_info = await self.extract_footer(None, html, footer_nav_items)
        except Exception:
            footer_info = None

        try:
            service_items, product_items = await self.extract_services_and_products(None, html, url)
        except Exception:
            service_items, product_items = [], []

        try:
            testimonials = await self.extract_testimonials(None, html, url)
        except Exception:
            testimonials = []

        try:
            team_members = await self.extract_team_members(None, html)
        except Exception:
            team_members = []

        try:
            faqs = await self.extract_faqs(None, html)
        except Exception:
            faqs = []

        company_info      = self.extract_company_info(html)
        trust_signal_list = self.extract_trust_signals(html)

        profile = WebsiteProfile(
            business=self._extract_business_info(soup, url),
            brand=brand,
            seo=self._extract_seo(soup, url),
            colors=color_palette,
            typography=self._extract_typography(computed),
            navigation=self._extract_navigation(soup, url),
            navigation_info=navigation_info_val,
            hero=self._extract_hero(soup),
            hero_info=hero_info_val,
            website_layout=WebsiteLayout(sections=sections, ctas=ctas, footer_info=footer_info),
            services=service_items or self._extract_services(soup),
            products=product_items,
            contact=self._extract_contact(soup),
            images=self._extract_images(soup, url),
            testimonials=testimonials,
            faqs=faqs,
            team=team_members or self._extract_team(soup),
            company=company_info,
            trust_signals=trust_signal_list,
            blog_links=self._extract_blog_links(soup),
            social_links=self._extract_social_links(soup, url),
            call_to_actions=self._extract_cta_buttons(soup, url),
            statistics=self._extract_statistics(soup),
            website_summary=self._build_website_summary(soup),
            raw_html_size_kb=raw_size_kb,
            extraction_timestamp=datetime.utcnow(),
        )

        profile.quality_metrics = self.calculate_quality_metrics(profile)
        profile.blueprint        = self.generate_website_blueprint(profile)

        existing = await website_intelligence_repository.get_by_lead(db, lead_id=lead.id)
        if existing:
            await website_intelligence_repository.update(db, lead_id=lead.id, profile=profile)
            logger.info("build_profile: intelligence updated | lead_id=%s", lead.id)
        else:
            await website_intelligence_repository.create(db, lead_id=lead.id, profile=profile)
            logger.info("build_profile: intelligence created | lead_id=%s", lead.id)

        logger.info(
            "build_profile: complete | lead_id=%s | total=%.1f s | html=%.0f KB | partial=%s",
            lead.id, _time.monotonic() - crawl_start,
            raw_size_kb, crawl_timed_out or crawl_blocked,
        )
        return profile

''')

# Indent the method body (4-space indent is already in the string)
# The file uses 4-space indentation throughout

src = TARGET.read_text(encoding="utf-8")

# Find the slice to replace
start_idx = src.find(START_MARKER)
if start_idx == -1:
    sys.exit("ERROR: START_MARKER not found in file")

end_idx = src.find("\n" + " " * 4 + END_MARKER.lstrip(), start_idx)
if end_idx == -1:
    sys.exit("ERROR: END_MARKER not found in file")
end_idx += 1  # include the leading newline before validate_profile

replacement = "    " + NEW_METHOD.replace("\n", "\n    ").rstrip() + "\n\n"

patched = src[:start_idx] + replacement + src[end_idx:]
TARGET.write_text(patched, encoding="utf-8")
print(f"Patched {TARGET} successfully. File size: {TARGET.stat().st_size:,} bytes")

# Quick syntax check
import py_compile
try:
    py_compile.compile(str(TARGET), doraise=True)
    print("Syntax OK")
except py_compile.PyCompileError as e:
    print(f"SYNTAX ERROR: {e}")
    sys.exit(1)
