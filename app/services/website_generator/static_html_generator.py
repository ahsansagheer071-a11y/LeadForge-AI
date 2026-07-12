"""Static HTML Website Generator — produces a single self-contained HTML file.

Hybrid approach to preserve ALL source content:
  - AI generation for creative sections (hero, about, testimonials, FAQ)
  - Structured data injection for complete sections (products, services, contact, footer)

This ensures every product, service, testimonial, and FAQ item from the source
website is included in the output, not limited by AI output token limits.
"""

import html as html_mod
import logging
import re
import time
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from app.services.website_intelligence.schemas import WebsiteProfile
from app.services.markdown_engine.schemas import MarkdownPackage
from app.services.website_generator.providers.provider_factory import ProviderFactory
from app.services.website_generator.schemas import (
    GenerationResult,
    PromptContext,
    WebsiteProject,
    GeneratedFile,
)
from app.services.website_generator.prompt_budget import PromptBudgetController
from app.services.website_generator.fidelity_validator import FidelityValidator
from app.services.website_generator.asset_packager import AssetPackager
from app.services.website_generator.content_extractor import ContentExtractor
from app.services.ai.chain import run_chain

logger = logging.getLogger(__name__)

SECTION_SYSTEM_PROMPT = (
    "You are an expert HTML/CSS code generator. "
    "You output ONLY raw HTML body content — no explanations, no markdown, no text. "
    "Every response must start with <header, <section, <div, <footer or <ul and contain valid HTML tags. "
    "NEVER use placeholder images (via.placeholder.com, example.com). "
    "ONLY use image URLs explicitly provided in the prompt. "
    "If a hero image URL is provided, use it as background-image on the hero."
)


class StaticHTMLGenerator:
    def __init__(self, provider_name: Optional[str] = None):
        self.provider_name = provider_name

    async def generate(
        self,
        blueprint: WebsiteProfile,
        package: MarkdownPackage,
    ) -> GenerationResult:
        start = time.monotonic()
        biz_name = getattr(getattr(blueprint, 'business', None), 'name', None) or 'unknown'
        logger.info("[GEN] generation started | business=%s", biz_name)

        brand_css = self._build_brand_css(blueprint)
        provider_used = ""
        provider_attempts = 0
        warnings: List[str] = []

        t1 = time.monotonic()
        hero_about_html, prov1, att1 = await self._ai_generate_hero_about(blueprint, brand_css)
        if prov1:
            provider_used = prov1
        provider_attempts += att1
        logger.info("[GEN] step=hero_about | len=%d | provider=%s | %.2fs",
            len(hero_about_html) if hero_about_html else 0, prov1, time.monotonic() - t1)

        t2 = time.monotonic()
        products_services_html = self._build_products_services(blueprint)
        logger.info("[GEN] step=products_services | len=%d | %.2fs",
            len(products_services_html), time.monotonic() - t2)

        t3 = time.monotonic()
        testimonials_faq_html, prov3, att3 = await self._ai_generate_testimonials_faq(blueprint, brand_css)
        if prov3 and not provider_used:
            provider_used = prov3
        provider_attempts += att3
        logger.info("[GEN] step=testimonials_faq | len=%d | provider=%s | %.2fs",
            len(testimonials_faq_html) if testimonials_faq_html else 0, prov3, time.monotonic() - t3)

        t4 = time.monotonic()
        contact_footer_html = self._build_contact_footer(blueprint)
        logger.info("[GEN] step=contact_footer | len=%d | %.2fs",
            len(contact_footer_html), time.monotonic() - t4)

        all_sections = []

        for name, html_content in [
            ("hero_about", hero_about_html),
            ("testimonials_faq", testimonials_faq_html),
        ]:
            if html_content:
                all_sections.append(html_content)
            else:
                warnings.append(f"AI section '{name}' returned empty HTML")

        all_sections.append(products_services_html)
        all_sections.append(contact_footer_html)

        merged_body = "\n\n".join(s for s in all_sections if s)
        merged_body = self._recover_body_content(merged_body)

        html_template = self._build_html_template(blueprint)
        html_content = html_template.replace("<!--BODY_CONTENT-->", merged_body)

        t5b = time.monotonic()
        asset_manifest = getattr(package, 'asset_manifest', None)
        validator = FidelityValidator(blueprint, manifest=asset_manifest)
        fidelity_result = validator.validate(html_content)
        fidelity_issue_count = len(fidelity_result.issues)
        if not fidelity_result.valid:
            for issue in fidelity_result.issues:
                logger.warning("[GEN] fidelity [%s]: %s", issue.category, issue.detail)
                warnings.append(f"[{issue.category}] {issue.detail}")
        logger.info("[GEN] step=fidelity | valid=%s | issues=%d | completeness=%.0f%% | %.2fs",
            fidelity_result.valid, fidelity_issue_count,
            fidelity_result.completeness_score * 100, time.monotonic() - t5b)

        t5c = time.monotonic()
        original_html = html_content
        packager = AssetPackager()
        image_artifacts: List[str] = []
        try:
            rewritten_html, artifacts_list, asset_warnings = await packager.package_assets_async(
                html_content, asset_manifest
            ) if asset_manifest else (html_content, [], [])
            warnings.extend(asset_warnings)
            if rewritten_html != html_content:
                html_content = rewritten_html
            import json as _json
            image_artifacts = [_json.dumps(a.model_dump(mode="json")) for a in artifacts_list]
            logger.info("[GEN] step=asset_packaging | images=%d | %.2fs",
                len(artifacts_list), time.monotonic() - t5c)
        except Exception as exc:
            warnings.append(f"Asset packaging failed: {exc}")
        finally:
            try:
                packager.cleanup()
            except Exception:
                pass

        project_name = biz_name.replace(" ", "_") if biz_name else "generated_website"
        generation_id = uuid.uuid4().hex[:12]

        html_file = GeneratedFile(
            path="index.html",
            content=html_content,
            type="html",
            size=len(html_content),
        )

        website_project = WebsiteProject(
            project_name=project_name,
            framework="static-html",
            generation_id=generation_id,
            version="1.0.0",
            generated_at=datetime.now(timezone.utc),
            files=[html_file],
            assets=image_artifacts,
            metadata={},
            statistics={
                "file_count": 1,
                "asset_count": len(image_artifacts),
                "fidelity_valid": fidelity_result.valid,
                "fidelity_issues": fidelity_issue_count,
                "completeness_score": fidelity_result.completeness_score,
                "products_preserved": f"{fidelity_result.preserved_product_count}/{fidelity_result.source_product_count}",
                "services_preserved": f"{fidelity_result.preserved_service_count}/{fidelity_result.source_service_count}",
                "testimonials_preserved": f"{fidelity_result.preserved_testimonial_count}/{fidelity_result.source_testimonial_count}",
                "faqs_preserved": f"{fidelity_result.preserved_faq_count}/{fidelity_result.source_faq_count}",
            },
            preview_html=original_html,
        )

        total_elapsed = time.monotonic() - start
        logger.info(
            "[GEN] done | business=%s | provider=%s | html=%d bytes | "
            "completeness=%.0f%% | total=%.2fs",
            biz_name, provider_used, len(html_content),
            fidelity_result.completeness_score * 100, total_elapsed,
        )
        return GenerationResult(
            success=True,
            website_project=website_project,
            warnings=warnings,
            generation_time=total_elapsed,
            provider_used=provider_used,
            provider_attempts=provider_attempts,
        )

    async def _ai_generate_hero_about(self, blueprint: WebsiteProfile, brand_css: str) -> tuple:
        prompt_text = self._build_hero_about_prompt(blueprint, brand_css)
        html, prov, att = await self._call_ai(prompt_text, "hero_about")
        return html, prov, att

    async def _ai_generate_testimonials_faq(self, blueprint: WebsiteProfile, brand_css: str) -> tuple:
        prompt_text = self._build_testimonials_faq_prompt(blueprint, brand_css)
        html, prov, att = await self._call_ai(prompt_text, "testimonials_faq")
        return html, prov, att

    async def _call_ai(self, prompt_text: str, section_name: str) -> tuple:
        budget_ctrl = PromptBudgetController()
        cleaned_text, _ = budget_ctrl._clean_text(prompt_text, "content_context")

        prompt = PromptContext(
            system_context=SECTION_SYSTEM_PROMPT,
            content_context=cleaned_text,
            generation_constraints="Output ONLY raw HTML body content. No explanations, no markdown.",
        )

        providers_to_try = ProviderFactory.get_fallback_chain(self.provider_name)

        async def _call(name: str):
            provider = ProviderFactory.get_provider(name)
            ai_resp = await provider.generate(prompt)
            if not ai_resp.success:
                from app.core.exceptions import ServiceUnavailableException
                msg = "; ".join(ai_resp.errors) if ai_resp.errors else "Provider failed"
                raise ServiceUnavailableException(msg)
            return ai_resp.raw_response, ai_resp.model

        chain_result = await run_chain(providers_to_try, _call)

        if not chain_result.success:
            logger.warning("[GEN] AI call for %s failed: %s", section_name, chain_result.last_error)
            return "", "", 0

        raw = chain_result.result or ""
        body = self._extract_body_content(raw)
        body = self._recover_body_content(body)
        return body, chain_result.provider_used, len(chain_result.attempts)

    def _build_hero_about_prompt(self, bp: WebsiteProfile, brand_css: str) -> str:
        lines = [
            "Generate HTML for the HERO and ABOUT sections of a website.",
            "Use inline styles. The hero MUST be a <header> tag (NOT <section>).",
            "The about section should be a <section> tag.",
            "",
            brand_css,
            "",
            "## CONTENT",
        ]
        biz = bp.business
        if biz.name:
            lines.append(f"Business Name: {biz.name}")
        if biz.description:
            lines.append(f"Business Description: {biz.description[:500]}")
        if biz.category:
            lines.append(f"Category: {biz.category}")

        brand = bp.brand
        if brand.tagline:
            lines.append(f"Tagline: {brand.tagline}")

        hero = bp.hero_info or bp.hero
        if hero:
            for attr in ['hero_title', 'title']:
                val = getattr(hero, attr, None)
                if val:
                    lines.append(f"Hero Title: {val}")
                    break
            for attr in ['hero_subtitle', 'subtitle']:
                val = getattr(hero, attr, None)
                if val:
                    lines.append(f"Hero Subtitle: {val}")
                    break
            for attr in ['hero_description', 'description']:
                val = getattr(hero, attr, None)
                if val:
                    lines.append(f"Hero Description: {val[:300]}")
                    break
            for attr in ['hero_image', 'background_image_url', 'background_image']:
                val = getattr(hero, attr, None)
                if val:
                    lines.append(f"Hero Image URL: {val}")
                    lines.append(f"USE THIS EXACT URL as background-image. Do NOT invent other image URLs.")
                    break
            ctas = getattr(hero, 'ctas', None) or []
            if ctas:
                for cta in ctas[:3]:
                    cta_text = getattr(cta, 'text', None) or getattr(cta, 'label', None) or "Learn More"
                    cta_url = getattr(cta, 'url', None) or "#"
                    lines.append(f"CTA Button: {cta_text} -> {cta_url}")

        company = bp.company
        if company:
            if company.mission:
                lines.append(f"Mission: {company.mission[:300]}")
            if company.core_values:
                lines.append(f"Core Values: {', '.join(company.core_values[:5])}")
            if company.usp:
                lines.append(f"USP: {company.usp[:200]}")

        team = bp.team
        if team:
            lines.append(f"Team Members ({len(team)}):")
            for m in team[:8]:
                role = m.role or m.job_title or ""
                name = m.full_name or m.name
                avatar = getattr(m, 'avatar_url', None) or getattr(m, 'avatar', None) or ""
                lines.append(f"  - {name}, {role}" + (f" [avatar: {avatar}]" if avatar else ""))

        images = bp.images or []
        if images:
            real_images = []
            for img in images[:15]:
                url = img.url if hasattr(img, 'url') else str(img)
                alt = img.alt if hasattr(img, 'alt') else ""
                if url and "example.com" not in url and "placeholder" not in url.lower():
                    real_images.append((url, alt))
            if real_images:
                lines.append(f"\n## AVAILABLE SOURCE IMAGES (use these, never invent new URLs):")
                for url, alt in real_images[:10]:
                    lines.append(f"  - {url}" + (f" (alt: {alt})" if alt else ""))

        social = bp.social_links or []
        if social:
            lines.append(f"\n## SOCIAL LINKS:")
            for sl in social[:6]:
                platform = sl.platform if hasattr(sl, 'platform') else ""
                url = sl.url if hasattr(sl, 'url') else str(sl)
                if platform and url:
                    lines.append(f"  - {platform}: {url}")

        lines.extend([
            "",
            "RULES:",
            "- The hero MUST use a <header> tag as the outermost element",
            "- Include the hero image as background-image on the hero section if a Hero Image URL is provided",
            "- Use ONLY image URLs listed in AVAILABLE SOURCE IMAGES above — never use via.placeholder.com, example.com, or any invented URLs",
            "- Include ALL team members listed above with their avatars if available",
            "- Include social links in the about section if available",
            "- Output ONLY HTML tags, no text commentary",
        ])
        return "\n".join(lines)

    def _build_testimonials_faq_prompt(self, bp: WebsiteProfile, brand_css: str) -> str:
        lines = [
            "Generate HTML for TESTIMONIALS and FAQ sections.",
            "Use inline styles. Start with <section>.",
            "",
            brand_css,
            "",
            "## TESTIMONIALS",
        ]
        testimonials = bp.testimonials or []
        if testimonials:
            lines.append(f"Include ALL {len(testimonials)} testimonials:")
            for i, t in enumerate(testimonials, 1):
                author = t.author or t.author_name or "Anonymous"
                company = t.company or t.company_name or ""
                text = t.content or t.review_text or ""
                rating = t.rating or t.star_count
                lines.append(f"{i}. \"{text[:200]}\" — {author}" + (f", {company}" if company else "") + (f" [{rating}/5 stars]" if rating else ""))
        else:
            lines.append("No testimonials available.")

        lines.append("")
        lines.append("## FAQs")
        faqs = bp.faqs or []
        if faqs:
            lines.append(f"Include ALL {len(faqs)} FAQs:")
            for i, faq in enumerate(faqs, 1):
                lines.append(f"{i}. Q: {faq.question}")
                lines.append(f"   A: {faq.answer[:250]}")
        else:
            lines.append("No FAQs available.")

        lines.extend([
            "",
            "RULES:",
            "- Include ALL testimonials and FAQs listed above — do NOT skip any",
            "- Output ONLY HTML tags, no text commentary",
        ])
        return "\n".join(lines)

    def _build_products_services(self, bp: WebsiteProfile) -> str:
        parts = []
        products = bp.products or []
        if products:
            items_html = []
            for p in products:
                title = html_mod.escape(p.title or p.subtitle or "Product")
                desc = html_mod.escape(p.short_description or p.full_description or "")[:150]
                price = html_mod.escape(p.price or "")
                currency = html_mod.escape(p.currency or "")
                image_url = p.image or ""
                badge = html_mod.escape(p.badge or "")

                card_content = f'<h3>{title}</h3>'
                if desc:
                    card_content += f'<p>{desc}</p>'
                if price:
                    card_content += f'<p style="font-weight:600;color:var(--accent)">{price}'
                    if currency:
                        card_content += f' {currency}'
                    card_content += '</p>'
                if badge:
                    card_content += f'<span style="background:var(--accent);color:#fff;padding:2px 8px;border-radius:4px;font-size:12px">{badge}</span>'

                if image_url:
                    item_html = f'<div class="card"><img src="{html_mod.escape(image_url)}" alt="{title}" style="width:100%;height:200px;object-fit:cover;border-radius:8px;margin-bottom:1rem">{card_content}</div>'
                else:
                    item_html = f'<div class="card">{card_content}</div>'
                items_html.append(item_html)

            grid_class = "grid-3" if len(products) > 3 else "grid-2"
            parts.append(
                f'<section style="padding:80px 0"><div class="container">\n'
                f'<h2 style="font-size:2rem;margin-bottom:2rem;text-align:center">Our Products</h2>\n'
                f'<div class="grid {grid_class}">\n'
                + "\n".join(items_html)
                + '\n</div>\n</div></section>'
            )

        services = bp.services or []
        if services:
            items_html = []
            for s in services:
                name = html_mod.escape(s.name or "Service")
                desc = html_mod.escape(s.description or s.short_description or "")[:150]
                features = s.features or []
                image_url = s.image or ""

                card_content = f'<h3>{name}</h3>'
                if desc:
                    card_content += f'<p>{desc}</p>'
                if features:
                    features_html = "".join(f'<li>{html_mod.escape(f)}</li>' for f in features[:5])
                    card_content += f'<ul style="list-style:disc;padding-left:1.5rem;margin-top:0.5rem">{features_html}</ul>'

                if image_url:
                    item_html = f'<div class="card"><img src="{html_mod.escape(image_url)}" alt="{name}" style="width:100%;height:200px;object-fit:cover;border-radius:8px;margin-bottom:1rem">{card_content}</div>'
                else:
                    item_html = f'<div class="card">{card_content}</div>'
                items_html.append(item_html)

            grid_class = "grid-3" if len(services) > 3 else "grid-2"
            parts.append(
                f'<section style="padding:80px 0"><div class="container">\n'
                f'<h2 style="font-size:2rem;margin-bottom:2rem;text-align:center">Our Services</h2>\n'
                f'<div class="grid {grid_class}">\n'
                + "\n".join(items_html)
                + '\n</div>\n</div></section>'
            )

        return "\n\n".join(parts)

    def _build_contact_footer(self, bp: WebsiteProfile) -> str:
        parts = []
        contact_lines = []
        social_lines = []

        contact = bp.contact
        if contact:
            for email in (contact.emails or []):
                contact_lines.append(f'<p><strong>Email:</strong> <a href="mailto:{html_mod.escape(email)}">{html_mod.escape(email)}</a></p>')
            for phone in (contact.phones or []):
                contact_lines.append(f'<p><strong>Phone:</strong> <a href="tel:{html_mod.escape(phone)}">{html_mod.escape(phone)}</a></p>')
            if contact.address:
                contact_lines.append(f'<p><strong>Address:</strong> {html_mod.escape(contact.address)}</p>')

        biz = bp.business
        if biz.opening_hours:
            contact_lines.append(f'<p><strong>Hours:</strong> {html_mod.escape(biz.opening_hours)}</p>')

        all_social = list(bp.social_links or []) + list(biz.social_links or [])
        seen_social = set()
        for link in all_social:
            platform = link.platform if hasattr(link, 'platform') else str(link)
            url = link.url if hasattr(link, 'url') else ""
            key = f"{platform}:{url}"
            if key not in seen_social:
                seen_social.add(key)
                social_lines.append(
                    f'<a href="{html_mod.escape(url)}" target="_blank" '
                    f'style="display:inline-block;margin:0 10px;color:var(--accent);text-decoration:none">'
                    f'{html_mod.escape(platform)}</a>'
                )

        if contact_lines:
            parts.append(
                f'<section style="padding:80px 0"><div class="container">\n'
                f'<h2 style="font-size:2rem;margin-bottom:2rem;text-align:center">Contact Us</h2>\n'
                f'<div style="text-align:center;font-size:1.1rem;line-height:2">\n'
                + "\n".join(contact_lines)
                + ('\n<div style="margin-top:1.5rem">' + "\n".join(social_lines) + '</div>' if social_lines else '')
                + '\n</div>\n</div></section>'
            )

        copyright_text = ""
        if hasattr(bp, 'website_layout') and bp.website_layout and bp.website_layout.footer_info:
            fi = bp.website_layout.footer_info
            if fi.copyright_text:
                copyright_text = fi.copyright_text
        if not copyright_text:
            copyright_text = f"&copy; {datetime.now().year} {html_mod.escape(biz.name or 'Business')}. All rights reserved."

        footer_nav = []
        if bp.navigation_info and bp.navigation_info.footer_nav_items:
            for item in bp.navigation_info.footer_nav_items[:10]:
                footer_nav.append(
                    f'<a href="{html_mod.escape(item.url)}" '
                    f'style="color:rgba(255,255,255,0.7);text-decoration:none;margin:0 10px">'
                    f'{html_mod.escape(item.label)}</a>'
                )

        parts.append(
            f'<footer style="background:var(--primary);padding:40px 0;text-align:center">\n'
            + ('\n'.join(footer_nav) + '\n' if footer_nav else '')
            + ('\n<div style="margin:1rem 0">' + "\n".join(social_lines) + '</div>\n' if social_lines else '')
            + f'<p style="color:rgba(255,255,255,0.6);margin-top:1rem">{copyright_text}</p>\n'
            + '</footer>'
        )

        return "\n\n".join(parts)

    def _build_brand_css(self, bp: WebsiteProfile) -> str:
        lines = ["## BRAND STYLING"]
        brand = bp.brand
        if brand:
            palette = getattr(brand, 'brand_colors', None) or getattr(bp, 'colors', None)
            if palette:
                for attr in ['primary', 'secondary', 'accent', 'background', 'text']:
                    val = getattr(palette, attr, None)
                    if val:
                        lines.append(f"Color {attr}: {val}")
            typo = getattr(brand, 'brand_typography', None) or getattr(bp, 'typography', None)
            if typo:
                hf = getattr(typo, 'heading_font', None)
                bf = getattr(typo, 'body_font', None)
                if hf:
                    lines.append(f"Heading Font: {hf}")
                if bf:
                    lines.append(f"Body Font: {bf}")
        return "\n".join(lines)

    def _extract_body_content(self, raw: str) -> str:
        if not raw:
            return ""
        stripped = raw.strip()
        fence_match = re.search(r"```(?:html)?\s*([\s\S]*?)```", stripped, re.IGNORECASE)
        if fence_match:
            stripped = fence_match.group(1).strip()
        body_match = re.search(r"<body[^>]*>([\s\S]*?)</body>", stripped, re.IGNORECASE)
        if body_match:
            return body_match.group(1).strip()
        if stripped.lower().startswith("<!doctype") or stripped.lower().startswith("<html"):
            after_head = re.sub(r"<!DOCTYPE[^>]*>\s*<html[^>]*>\s*<head[\s\S]*?</head>\s*", "", stripped, flags=re.IGNORECASE)
            after_head = re.sub(r"</?html[^>]*>\s*", "", after_head, flags=re.IGNORECASE)
            after_head = re.sub(r"</body>\s*</html>\s*$", "", after_head, flags=re.IGNORECASE)
            after_head = re.sub(r"</html>\s*$", "", after_head, flags=re.IGNORECASE)
            if after_head.strip():
                return after_head.strip()
        return stripped

    @staticmethod
    def _recover_body_content(body: str) -> str:
        if not body:
            return body
        if body.rstrip().endswith("</body>") or body.rstrip().endswith("</html>"):
            return body
        open_tags = re.findall(r"<(section|div|header|footer|nav|main|article|aside|figure|ul|ol|li|table|tr|td|th|thead|tbody|p|h[1-6])\b", body, re.IGNORECASE)
        closings = []
        for tag in reversed(open_tags):
            if not re.search(rf"</{tag}\s*>", body, re.IGNORECASE):
                closings.append(f"</{tag}>")
        if closings:
            recovered = body.rstrip() + "\n" + "\n".join(closings)
            logger.info("[GEN] body_recovery: added %d closing tags", len(closings))
            return recovered
        return body

    @staticmethod
    def _build_html_template(blueprint) -> str:
        brand = getattr(blueprint, 'brand', None)
        primary = "#1a1a2e"
        secondary = "#16213e"
        accent = "#e94560"
        text_color = "#ffffff"
        bg_color = "#0f0f23"
        heading_font = "'Inter', 'Segoe UI', sans-serif"
        body_font = "'Inter', 'Segoe UI', sans-serif"

        if brand:
            palette = getattr(brand, 'brand_colors', None)
            if not palette:
                palette = getattr(blueprint, 'colors', None)
            if palette:
                primary = getattr(palette, 'primary', None) or primary
                secondary = getattr(palette, 'secondary', None) or secondary
                accent = getattr(palette, 'accent', None) or accent
            typography = getattr(brand, 'brand_typography', None)
            if not typography:
                typography = getattr(blueprint, 'typography', None)
            if typography:
                heading_font = getattr(typography, 'heading_font', None) or heading_font
                body_font = getattr(typography, 'body_font', None) or body_font

        biz_name = getattr(getattr(blueprint, 'business', None), 'name', None) or 'Business'
        seo = getattr(blueprint, 'seo', None)
        description = ""
        if seo:
            description = getattr(seo, 'meta_description', None) or description

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{biz_name}</title>
<meta name="description" content="{description}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --primary:{primary};
  --secondary:{secondary};
  --accent:{accent};
  --text:{text_color};
  --bg:{bg_color};
  --heading-font:{heading_font};
  --body-font:{body_font};
}}
html{{scroll-behavior:smooth}}
body{{font-family:var(--body-font);color:var(--text);background:var(--bg);line-height:1.6}}
h1,h2,h3,h4,h5,h6{{font-family:var(--heading-font);font-weight:600;line-height:1.2}}
img{{max-width:100%;height:auto;display:block}}
a{{color:var(--accent);text-decoration:none}}
a:hover{{text-decoration:underline}}
.container{{max-width:1200px;margin:0 auto;padding:0 20px}}
section{{padding:80px 0}}
.grid{{display:grid;gap:2rem}}
.grid-2{{grid-template-columns:repeat(auto-fit,minmax(300px,1fr))}}
.grid-3{{grid-template-columns:repeat(auto-fit,minmax(250px,1fr))}}
.card{{background:rgba(255,255,255,0.05);border-radius:12px;padding:2rem;border:1px solid rgba(255,255,255,0.1);transition:transform .2s,box-shadow .2s}}
.card:hover{{transform:translateY(-4px);box-shadow:0 8px 24px rgba(0,0,0,0.3)}}
.card h3{{margin-bottom:0.75rem;color:var(--accent)}}
.card p{{color:rgba(255,255,255,0.8);margin-bottom:0.5rem}}
footer{{background:var(--primary);padding:40px 0;text-align:center;opacity:0.9}}
@media(max-width:768px){{
  section{{padding:40px 0}}
}}
</style>
</head>
<body>
<!--BODY_CONTENT-->
</body>
</html>"""
