"""PremiumRedesignBrief generator.

Takes a WebsiteProfile + optional audit weaknesses
and produces a world-class UX agency redesign instruction
that lets Stitch understand and redesign the source website.

The brief tells Stitch WHAT to redesign, not HOW to reconstruct.
Stitch crawls the URL itself — we don't dump extracted content.
"""

import hashlib
import logging
from typing import Any, Dict, List, Optional

from app.services.website_intelligence.schemas import WebsiteProfile
from app.services.website_generator.stitch.schemas import (
    PremiumRedesignBrief,
    StitchBriefSection,
    StitchDesignTokens,
)

logger = logging.getLogger(__name__)


class BriefGenerator:
    """Generates a PremiumRedesignBrief from lead intelligence data.

    The brief is a concise, world-class UX agency instruction.
    It gives Stitch the URL, the business context, audit weaknesses,
    and design direction — then lets Stitch do what it does best.
    """

    def generate(
        self,
        profile: WebsiteProfile,
        package: Any = None,
        weaknesses: Optional[List[str]] = None,
        recommendations: Optional[List[str]] = None,
    ) -> PremiumRedesignBrief:
        logger.info(
            "[BriefGenerator] Generating brief for %s",
            profile.business.name or profile.business.website_url,
        )

        tokens = self._extract_design_tokens(profile)
        hero = self._build_hero_section(profile)
        sections = self._build_content_sections(profile)
        nav = self._build_navigation(profile)
        contact = self._build_contact_info(profile)
        social = self._build_social_links(profile)
        images = self._collect_original_images(profile)

        brief = PremiumRedesignBrief(
            business_name=profile.business.name or "Unknown Business",
            business_url=profile.business.website_url or "",
            business_category=profile.business.category or profile.business.industry or "",
            business_description=profile.business.description or "",
            design_direction="premium modern responsive",
            design_tokens=tokens,
            hero_section=hero,
            sections=sections,
            navigation_items=nav,
            contact_info=contact,
            social_links=social,
            original_images=images,
            logo_url=profile.brand.logo_info.logo_url if profile.brand and profile.brand.logo_info else "",
            content_rules=self._build_content_rules(profile),
            design_rules=self._build_design_rules(profile, weaknesses, recommendations),
            source_content_summary=self._build_source_summary(profile),
        )

        brief.full_instruction = self._compile_instruction(brief, weaknesses, recommendations)

        logger.info(
            "[BriefGenerator] Brief generated: %d chars instruction",
            len(brief.full_instruction),
        )

        return brief

    def _extract_design_tokens(self, profile: WebsiteProfile) -> StitchDesignTokens:
        colors = profile.colors
        if not colors or not colors.primary:
            if profile.brand and profile.brand.brand_colors:
                colors = profile.brand.brand_colors
        typo = profile.typography
        if not typo or not typo.heading_font:
            if profile.brand and profile.brand.brand_typography:
                typo = profile.brand.brand_typography
        logo_info = profile.brand.logo_info if profile.brand else None

        return StitchDesignTokens(
            primary_color=colors.primary if colors else None,
            secondary_color=colors.secondary if colors else None,
            accent_color=colors.accent if colors else None,
            background_color=colors.background if colors else None,
            text_color=colors.text if colors else None,
            heading_font=typo.heading_font if typo else None,
            body_font=typo.body_font if typo else None,
            logo_url=logo_info.logo_url if logo_info else None,
            favicon_url=profile.business.favicon if profile.business else None,
        )

    def _build_hero_section(self, profile: WebsiteProfile) -> StitchBriefSection:
        hero_info = profile.hero_info
        hero = profile.hero

        title = ""
        subtitle = ""
        cta_text = ""
        source_images = []

        if hero_info:
            title = hero_info.hero_title or hero_info.title or ""
            subtitle = hero_info.hero_subtitle or hero_info.hero_description or hero_info.subtitle or ""
            if hero_info.ctas:
                cta_text = hero_info.ctas[0].text if hero_info.ctas else ""
            elif hero_info.primary_cta:
                cta_text = hero_info.primary_cta.text
            if hero_info.hero_image:
                source_images.append(hero_info.hero_image)
            if hero_info.background_image_url:
                source_images.append(hero_info.background_image_url)
        elif hero:
            title = hero.title or ""
            subtitle = hero.subtitle or ""
            if hero.cta_buttons:
                first_cta = hero.cta_buttons[0]
                cta_text = first_cta.get("text", "") if isinstance(first_cta, dict) else ""
            if hero.background_image:
                source_images.append(hero.background_image)

        content_parts = []
        if title:
            content_parts.append(f"Headline: {title}")
        if subtitle:
            content_parts.append(f"Subtitle: {subtitle}")
        if cta_text:
            content_parts.append(f"Primary CTA: {cta_text}")

        return StitchBriefSection(
            section_type="hero",
            title="Hero Section",
            content_instructions="\n".join(content_parts) if content_parts else "Use the business name as the hero headline with a compelling tagline.",
            source_content=content_parts,
            source_images=source_images,
            design_notes="Full-width hero with background image, overlay text, and prominent CTA button.",
        )

    def _build_content_sections(self, profile: WebsiteProfile) -> List[StitchBriefSection]:
        sections = []

        if profile.services:
            svc_names = [s.name for s in profile.services if s.name]
            sections.append(StitchBriefSection(
                section_type="services",
                title="Services",
                content_instructions=f"Services offered: {', '.join(svc_names)}",
                source_content=svc_names,
                design_notes="Card-based layout with icon/image, title, and description for each service.",
            ))

        if profile.products:
            prod_names = [p.title for p in profile.products if p.title]
            sections.append(StitchBriefSection(
                section_type="products",
                title="Products",
                content_instructions=f"Products offered: {', '.join(prod_names)}",
                source_content=prod_names,
                design_notes="Grid layout with product cards, images, and pricing.",
            ))

        if profile.testimonials:
            sections.append(StitchBriefSection(
                section_type="testimonials",
                title="Testimonials",
                content_instructions=f"{len(profile.testimonials)} customer testimonials available on the source website.",
                source_content=[],
                design_notes="Carousel or grid of testimonial cards with quote, author, and rating.",
            ))

        if profile.faqs:
            sections.append(StitchBriefSection(
                section_type="faq",
                title="FAQ",
                content_instructions=f"{len(profile.faqs)} FAQs available on the source website.",
                source_content=[],
                design_notes="Accordion-style FAQ with expandable questions and answers.",
            ))

        if profile.company:
            company = profile.company
            about_parts = []
            if company.description:
                about_parts.append(company.description)
            if company.mission:
                about_parts.append(f"Our Mission: {company.mission}")
            if about_parts:
                sections.append(StitchBriefSection(
                    section_type="about",
                    title="About Us",
                    content_instructions="\n\n".join(about_parts),
                    source_content=about_parts,
                    design_notes="About section with company story, mission, and values.",
                ))

        return sections

    def _build_navigation(self, profile: WebsiteProfile) -> List[Dict[str, str]]:
        nav_items = []
        if profile.navigation_info and profile.navigation_info.primary_nav_items:
            for item in profile.navigation_info.primary_nav_items[:10]:
                nav_items.append({"label": item.label, "url": item.url})
        elif profile.navigation:
            for item in profile.navigation[:10]:
                nav_items.append({"label": item.label, "url": item.url})
        if not nav_items:
            nav_items = [
                {"label": "Home", "url": "/"},
                {"label": "About", "url": "#about"},
                {"label": "Services", "url": "#services"},
                {"label": "Contact", "url": "#contact"},
            ]
        return nav_items

    def _build_contact_info(self, profile: WebsiteProfile) -> Dict[str, str]:
        info = {}
        if profile.contact:
            if profile.contact.emails:
                info["email"] = profile.contact.emails[0]
            if profile.contact.phones:
                info["phone"] = profile.contact.phones[0]
            if profile.contact.address:
                info["address"] = profile.contact.address
        if profile.business:
            if not info.get("email") and profile.business.email:
                info["email"] = profile.business.email
            if not info.get("phone") and profile.business.phone:
                info["phone"] = profile.business.phone
            if not info.get("address") and profile.business.address:
                info["address"] = profile.business.address
        return info

    def _build_social_links(self, profile: WebsiteProfile) -> List[Dict[str, str]]:
        links = []
        source = profile.social_links or []
        if not source and profile.business and profile.business.social_links:
            source = profile.business.social_links
        if profile.website_layout and profile.website_layout.footer_info:
            source = source + (profile.website_layout.footer_info.social_links or [])
        for link in source:
            links.append({"platform": link.platform, "url": link.url})
        return links

    def _collect_original_images(self, profile: WebsiteProfile) -> List[Dict[str, str]]:
        images = []
        seen = set()

        def add(url: Optional[str], role: str = "other"):
            if not url or url in seen:
                return
            seen.add(url)
            images.append({"url": url, "role": role})

        if profile.brand and profile.brand.logo_info:
            add(profile.brand.logo_info.logo_url, "logo")
        if profile.business:
            add(profile.business.logo, "logo")
            add(profile.business.favicon, "favicon")
        if profile.hero_info:
            add(profile.hero_info.hero_image, "hero")
            add(profile.hero_info.background_image_url, "hero-bg")
        for img in (profile.images or []):
            add(img.url, "source")

        return images

    def _build_content_rules(self, profile: WebsiteProfile) -> List[str]:
        return [
            "PRESERVE all original business content exactly as written",
            "PRESERVE the original logo and all source images",
            "DO NOT invent services, products, testimonials, or claims",
            "DO NOT use Lorem Ipsum or placeholder text of any kind",
            "DO NOT add LeadForge branding or references",
            "DO NOT add fake contact details, dummy emails, or example addresses",
            "DO NOT fabricate team members, awards, or certifications",
        ]

    def _build_design_rules(
        self,
        profile: WebsiteProfile,
        weaknesses: Optional[List[str]] = None,
        recommendations: Optional[List[str]] = None,
    ) -> List[str]:
        rules = [
            "Create a premium, modern, production-ready responsive website",
            "Ensure mobile-first responsive design",
            "Use clean typography with clear visual hierarchy",
            "Ensure color contrast meets WCAG AA accessibility",
            "Include smooth scroll and subtle hover effects",
            "Include a sticky navigation bar",
            "Include a hero section with prominent CTA",
            "Include a footer with contact info and social links",
            "Optimize for performance — no heavy frameworks, minimal JS",
        ]

        typo = profile.typography or (profile.brand.brand_typography if profile.brand else None)
        if typo and typo.heading_font:
            rules.append(f"Use heading font: {typo.heading_font}")
        if typo and typo.body_font:
            rules.append(f"Use body font: {typo.body_font}")

        colors = profile.colors or (profile.brand.brand_colors if profile.brand else None)
        if colors and colors.primary:
            rules.append(f"Primary brand color: {colors.primary}")
        if colors and colors.secondary:
            rules.append(f"Secondary brand color: {colors.secondary}")

        return rules

    def _build_source_summary(self, profile: WebsiteProfile) -> str:
        parts = []
        if profile.business.name:
            parts.append(f"Business: {profile.business.name}")
        if profile.business.category:
            parts.append(f"Category: {profile.business.category}")
        return "\n".join(parts)

    def _compile_instruction(
        self,
        brief: PremiumRedesignBrief,
        weaknesses: Optional[List[str]] = None,
        recommendations: Optional[List[str]] = None,
    ) -> str:
        parts = []

        # ── ROLE ──────────────────────────────────────────────────────────
        parts.append("# ROLE")
        parts.append("")
        parts.append("You are an award-winning senior UI/UX designer.")
        parts.append("You specialize in premium business website redesigns.")
        parts.append("Your task is NOT to create a new business.")
        parts.append("Your task is to redesign the existing website.")
        parts.append("")

        # ── SOURCE WEBSITE ────────────────────────────────────────────────
        parts.append("# SOURCE WEBSITE")
        parts.append("")
        parts.append(f"Website URL: {brief.business_url}")
        parts.append(f"Business Name: {brief.business_name}")
        if brief.business_category:
            parts.append(f"Category: {brief.business_category}")
        if brief.business_description:
            parts.append(f"Description: {brief.business_description}")
        parts.append("")
        parts.append("Visit and study the website above before redesigning.")
        parts.append("")

        # ── BUSINESS RULES ────────────────────────────────────────────────
        parts.append("# BUSINESS RULES")
        parts.append("")
        parts.append("Use the existing website as the source of truth.")
        parts.append("")
        parts.append("PRESERVE:")
        parts.append("- business identity")
        parts.append("- products")
        parts.append("- services")
        parts.append("- contact information")
        parts.append("- branding")
        parts.append("- messaging")
        parts.append("- images whenever appropriate")
        parts.append("")
        parts.append("NEVER INVENT:")
        parts.append("- companies")
        parts.append("- products")
        parts.append("- testimonials")
        parts.append("- addresses")
        parts.append("- emails")
        parts.append("- phone numbers")
        parts.append("- fake reviews")
        parts.append("- fake awards")
        parts.append("")

        # ── OBJECTIVE ─────────────────────────────────────────────────────
        parts.append("# OBJECTIVE")
        parts.append("")
        parts.append("Create a premium redesign of the existing website.")
        parts.append("")
        parts.append("IMPROVE ONLY:")
        parts.append("- UI")
        parts.append("- UX")
        parts.append("- layout")
        parts.append("- hierarchy")
        parts.append("- typography")
        parts.append("- spacing")
        parts.append("- responsiveness")
        parts.append("- accessibility")
        parts.append("- trust")
        parts.append("- conversion")
        parts.append("- interactions")
        parts.append("- animations")
        parts.append("")
        parts.append("Keep the same business. Do not change what the company does.")
        parts.append("")

        # ── BRAND IDENTITY ────────────────────────────────────────────────
        tokens = brief.design_tokens
        has_brand = any([tokens.primary_color, tokens.secondary_color, tokens.heading_font, tokens.body_font])
        if has_brand:
            parts.append("# BRAND IDENTITY")
            parts.append("")
            if tokens.primary_color:
                parts.append(f"Primary color: {tokens.primary_color}")
            if tokens.secondary_color:
                parts.append(f"Secondary color: {tokens.secondary_color}")
            if tokens.accent_color:
                parts.append(f"Accent color: {tokens.accent_color}")
            if tokens.heading_font:
                parts.append(f"Heading font: {tokens.heading_font}")
            if tokens.body_font:
                parts.append(f"Body font: {tokens.body_font}")
            if brief.logo_url:
                parts.append(f"Logo: {brief.logo_url}")
            parts.append("")
            parts.append("Respect and enhance the existing brand identity.")
            parts.append("")

        # ── AUDIT IMPROVEMENTS ────────────────────────────────────────────
        all_weaknesses = list(weaknesses or [])
        if recommendations:
            all_weaknesses.extend(recommendations)

        if all_weaknesses:
            parts.append("# AUDIT IMPROVEMENTS")
            parts.append("")
            parts.append("The following issues were identified in the current website.")
            parts.append("Address each one in your redesign:")
            parts.append("")
            for w in all_weaknesses[:10]:
                parts.append(f"- {w}")
            parts.append("")

        # ── DESIGN DIRECTION ──────────────────────────────────────────────
        parts.append("# DESIGN DIRECTION")
        parts.append("")
        parts.append("Think:")
        parts.append("- Apple")
        parts.append("- Stripe")
        parts.append("- Linear")
        parts.append("- Framer")
        parts.append("- Webflow Enterprise")
        parts.append("- Awwwards")
        parts.append("")
        parts.append("Minimal. Elegant. Premium. Fast. Modern. Clean. Accessible.")
        parts.append("Premium SaaS quality applied to this business.")
        parts.append("")

        # ── CONTENT HIGHLIGHTS ────────────────────────────────────────────
        if brief.sections:
            parts.append("# CONTENT HIGHLIGHTS")
            parts.append("")
            parts.append("Key content from the source website to include:")
            parts.append("")
            for section in brief.sections:
                parts.append(f"- {section.title}: {section.content_instructions}")
            parts.append("")

        if brief.contact_info:
            parts.append("# CONTACT INFORMATION")
            parts.append("")
            for key, val in brief.contact_info.items():
                parts.append(f"- {key.title()}: {val}")
            parts.append("")

        # ── OUTPUT ────────────────────────────────────────────────────────
        parts.append("# OUTPUT")
        parts.append("")
        parts.append("Return a production-ready premium redesign as a single self-contained HTML file with embedded CSS.")
        parts.append("- Responsive design (mobile-first)")
        parts.append("- Semantic HTML5 structure")
        parts.append("- No external CSS/JS frameworks — use vanilla CSS")
        parts.append("- All images referenced by their original URLs from the source website")
        parts.append("- Premium, polished, and visually stunning")
        parts.append("")

        return "\n".join(parts)

    def brief_hash(self, brief: PremiumRedesignBrief) -> str:
        return hashlib.sha256(brief.full_instruction.encode("utf-8")).hexdigest()[:16]
