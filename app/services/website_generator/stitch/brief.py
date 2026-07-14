"""PremiumRedesignBrief generator.

Takes a WebsiteProfile + MarkdownPackage + optional audit weaknesses
and produces a complete Stitch redesign instruction that preserves
all original content, images, and business identity.
"""

import hashlib
import logging
from typing import Any, Dict, List, Optional

from app.services.markdown_engine.schemas import MarkdownPackage
from app.services.website_intelligence.schemas import WebsiteProfile
from app.services.website_generator.stitch.schemas import (
    PremiumRedesignBrief,
    StitchBriefSection,
    StitchDesignTokens,
)

logger = logging.getLogger(__name__)


class BriefGenerator:
    """Generates a PremiumRedesignBrief from lead intelligence data."""

    def generate(
        self,
        profile: WebsiteProfile,
        package: Optional[MarkdownPackage] = None,
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
        content_rules = self._build_content_rules(profile)
        design_rules = self._build_design_rules(profile, weaknesses, recommendations)
        source_summary = self._build_source_summary(profile, package)

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
            content_rules=content_rules,
            design_rules=design_rules,
            source_content_summary=source_summary,
        )

        brief.full_instruction = self._compile_instruction(brief)

        logger.info(
            "[BriefGenerator] Brief generated: %d sections, %d images, %d rules",
            len(brief.sections),
            len(brief.original_images),
            len(brief.content_rules) + len(brief.design_rules),
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
            svc_items = []
            svc_images = []
            for svc in profile.services:
                parts = [f"**{svc.name}**"]
                if svc.description:
                    parts.append(svc.description)
                if svc.features:
                    parts.extend([f"- {f}" for f in svc.features[:5]])
                svc_items.append("\n".join(parts))
                if svc.image:
                    svc_images.append(svc.image)
            sections.append(StitchBriefSection(
                section_type="services",
                title="Services",
                content_instructions="\n\n".join(svc_items),
                source_content=svc_items,
                source_images=svc_images,
                design_notes="Card-based layout with icon/image, title, and description for each service.",
            ))

        if profile.products:
            prod_items = []
            prod_images = []
            for prod in profile.products:
                parts = [f"**{prod.title or 'Product'}**"]
                if prod.short_description:
                    parts.append(prod.short_description)
                if prod.price:
                    parts.append(f"Price: {prod.price}")
                prod_items.append("\n".join(parts))
                if prod.image:
                    prod_images.append(prod.image)
            sections.append(StitchBriefSection(
                section_type="products",
                title="Products",
                content_instructions="\n\n".join(prod_items),
                source_content=prod_items,
                source_images=prod_images,
                design_notes="Grid layout with product cards, images, and pricing.",
            ))

        if profile.testimonials:
            test_items = []
            for t in profile.testimonials[:6]:
                author = t.author_name or t.author or "Customer"
                content = t.review_text or t.content or ""
                rating = f" ({t.star_count}/5)" if t.star_count else ""
                test_items.append(f'"{content}" — {author}{rating}')
            sections.append(StitchBriefSection(
                section_type="testimonials",
                title="Testimonials",
                content_instructions="\n\n".join(test_items),
                source_content=test_items,
                design_notes="Carousel or grid of testimonial cards with quote, author, and rating.",
            ))

        if profile.faqs:
            faq_items = []
            for faq in profile.faqs[:10]:
                faq_items.append(f"**Q: {faq.question}**\nA: {faq.answer}")
            sections.append(StitchBriefSection(
                section_type="faq",
                title="FAQ",
                content_instructions="\n\n".join(faq_items),
                source_content=faq_items,
                design_notes="Accordion-style FAQ with expandable questions and answers.",
            ))

        if profile.team:
            team_items = []
            team_images = []
            for member in profile.team[:8]:
                name = member.full_name or member.name
                parts = [f"**{name}**"]
                if member.role or member.job_title:
                    parts.append(member.role or member.job_title)
                if member.bio:
                    parts.append(member.bio)
                team_items.append("\n".join(parts))
                img = member.photo_url or member.image
                if img:
                    team_images.append(img)
            sections.append(StitchBriefSection(
                section_type="team",
                title="Team",
                content_instructions="\n\n".join(team_items),
                source_content=team_items,
                source_images=team_images,
                design_notes="Team member cards with photo, name, role, and bio.",
            ))

        if profile.company:
            company = profile.company
            about_parts = []
            if company.description:
                about_parts.append(company.description)
            if company.mission:
                about_parts.append(f"Our Mission: {company.mission}")
            if company.vision:
                about_parts.append(f"Our Vision: {company.vision}")
            if company.core_values:
                about_parts.append(f"Core Values: {', '.join(company.core_values)}")
            if about_parts:
                sections.append(StitchBriefSection(
                    section_type="about",
                    title="About Us",
                    content_instructions="\n\n".join(about_parts),
                    source_content=about_parts,
                    design_notes="About section with company story, mission, and values.",
                ))

        if profile.trust_signals:
            trust_items = [f"- {ts.value}" for ts in profile.trust_signals[:6]]
            sections.append(StitchBriefSection(
                section_type="trust",
                title="Trust Signals",
                content_instructions="\n".join(trust_items),
                source_content=trust_items,
                design_notes="Trust badges or awards section.",
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
        for svc in (profile.services or []):
            add(svc.image, "service")
        for prod in (profile.products or []):
            add(prod.image, "product")
        for t in (profile.testimonials or []):
            add(t.avatar or t.avatar_url, "testimonial")
        for m in (profile.team or []):
            add(m.photo_url or m.image, "team")
        for img in (profile.images or []):
            add(img.url, "source")

        return images

    def _build_content_rules(self, profile: WebsiteProfile) -> List[str]:
        rules = [
            "PRESERVE all original business content exactly as written",
            "PRESERVE the original logo and all source images",
            "DO NOT invent services, products, testimonials, or claims",
            "DO NOT use Lorem Ipsum or placeholder text of any kind",
            "DO NOT add LeadForge branding or references",
            "DO NOT add fake contact details, dummy emails, or example addresses",
            "DO NOT fabricate team members, awards, or certifications",
            "Use ONLY the source content, images, and business data provided",
        ]
        return rules

    def _build_design_rules(
        self,
        profile: WebsiteProfile,
        weaknesses: Optional[List[str]] = None,
        recommendations: Optional[List[str]] = None,
    ) -> List[str]:
        rules = [
            "Create a premium, modern, production-ready responsive website",
            "Ensure mobile-first responsive design (works on all screen sizes)",
            "Use clean typography with clear visual hierarchy (H1 > H2 > H3)",
            "Use adequate white space and padding for readability",
            "Ensure color contrast meets WCAG AA accessibility standards",
            "Include smooth scroll behavior and subtle hover effects",
            "Use CSS Grid or Flexbox for responsive layouts",
            "Include a sticky/fixed navigation bar",
            "Include a hero section with prominent call-to-action",
            "Include a footer with contact info, social links, and copyright",
            "Optimize for performance (no heavy frameworks, minimal JS)",
        ]
        if weaknesses:
            for w in weaknesses[:5]:
                rules.append(f"ADDRESS weakness: {w}")
        if recommendations:
            for r in recommendations[:5]:
                rules.append(f"IMPLEMENT recommendation: {r}")

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

    def _build_source_summary(self, profile: WebsiteProfile, package: Optional[MarkdownPackage]) -> str:
        parts = []
        if profile.business.name:
            parts.append(f"Business: {profile.business.name}")
        if profile.business.category:
            parts.append(f"Category: {profile.business.category}")
        if profile.services:
            parts.append(f"Services: {', '.join(s.name for s in profile.services[:10])}")
        if profile.products:
            parts.append(f"Products: {', '.join(p.title for p in profile.products[:10] if p.title)}")
        if profile.testimonials:
            parts.append(f"Testimonials: {len(profile.testimonials)} found")
        if profile.faqs:
            parts.append(f"FAQs: {len(profile.faqs)} found")
        if profile.images:
            parts.append(f"Source images: {len(profile.images)} found")
        if profile.contact:
            if profile.contact.emails:
                parts.append(f"Contact: {', '.join(profile.contact.emails[:3])}")
        return "\n".join(parts)

    def _compile_instruction(self, brief: PremiumRedesignBrief) -> str:
        parts = []

        parts.append(f"# Premium Website Redesign Brief for {brief.business_name}")
        parts.append("")
        parts.append(f"**Source URL:** {brief.business_url}")
        if brief.business_category:
            parts.append(f"**Category:** {brief.business_category}")
        if brief.business_description:
            parts.append(f"**Description:** {brief.business_description}")
        parts.append("")

        parts.append("## Design Direction")
        parts.append(brief.design_direction)
        parts.append("")

        tokens = brief.design_tokens
        token_parts = []
        if tokens.primary_color:
            token_parts.append(f"Primary: {tokens.primary_color}")
        if tokens.secondary_color:
            token_parts.append(f"Secondary: {tokens.secondary_color}")
        if tokens.accent_color:
            token_parts.append(f"Accent: {tokens.accent_color}")
        if tokens.heading_font:
            token_parts.append(f"Heading font: {tokens.heading_font}")
        if tokens.body_font:
            token_parts.append(f"Body font: {tokens.body_font}")
        if token_parts:
            parts.append("**Brand Colors & Typography:** " + " | ".join(token_parts))
            parts.append("")

        if brief.logo_url:
            parts.append(f"**Logo URL:** {brief.logo_url}")
            parts.append("")

        parts.append("## Content Rules (MANDATORY)")
        for rule in brief.content_rules:
            parts.append(f"- {rule}")
        parts.append("")

        parts.append("## Design Rules (MANDATORY)")
        for rule in brief.design_rules:
            parts.append(f"- {rule}")
        parts.append("")

        parts.append("## Navigation")
        for item in brief.navigation_items:
            parts.append(f"- [{item.get('label', '')}]({item.get('url', '')})")
        parts.append("")

        parts.append("## Hero Section")
        parts.append(brief.hero_section.content_instructions)
        if brief.hero_section.source_images:
            parts.append("**Hero images:**")
            for img in brief.hero_section.source_images:
                parts.append(f"  - {img}")
        parts.append("")

        for section in brief.sections:
            parts.append(f"## {section.title}")
            parts.append(section.content_instructions)
            if section.source_images:
                parts.append("**Images for this section:**")
                for img in section.source_images[:5]:
                    parts.append(f"  - {img}")
            if section.design_notes:
                parts.append(f"*Design note: {section.design_notes}*")
            parts.append("")

        if brief.original_images:
            parts.append("## Original Images (USE THESE)")
            parts.append("The following images are from the source website and MUST be used in the redesign:")
            for img in brief.original_images[:30]:
                parts.append(f"- [{img.get('role', 'image')}]({img.get('url', '')})")
            parts.append("")

        if brief.contact_info:
            parts.append("## Contact Information")
            for key, val in brief.contact_info.items():
                parts.append(f"- **{key.title()}:** {val}")
            parts.append("")

        if brief.social_links:
            parts.append("## Social Links")
            for link in brief.social_links:
                parts.append(f"- [{link.get('platform', '')}]({link.get('url', '')})")
            parts.append("")

        parts.append("## Output Requirements")
        parts.append("- Single self-contained HTML file with embedded CSS")
        parts.append("- Responsive design (mobile-first)")
        parts.append("- Semantic HTML5 structure")
        parts.append("- No external CSS/JS frameworks (use vanilla CSS)")
        parts.append("- All images referenced by their original URLs")
        parts.append("- Production-ready, polished, and visually premium")
        parts.append("")

        return "\n".join(parts)

    def brief_hash(self, brief: PremiumRedesignBrief) -> str:
        return hashlib.sha256(brief.full_instruction.encode("utf-8")).hexdigest()[:16]
