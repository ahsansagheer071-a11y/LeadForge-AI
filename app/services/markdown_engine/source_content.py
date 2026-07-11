"""Canonical source website content model and markdown builder.

Extracts the actual verbatim content from WebsiteProfile and formats it
as structured markdown.  No analysis, no derivation, no summarization.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.services.markdown_engine.asset_manifest import AssetManifest, AssetRole
from app.services.website_intelligence.schemas import (
    BusinessInfo,
    CallToAction,
    CompanySection,
    ContactInfo,
    FAQ,
    FooterInfo,
    HeroInfo,
    ImageAsset,
    NavItem,
    NavigationInfo,
    ProductItem,
    ServiceCard,
    SocialLink,
    TeamMember,
    Testimonial,
    WebsiteLayout,
    WebsiteProfile,
)


# ---------------------------------------------------------------------------
# Canonical snapshot — no analysis fields, only verbatim source content
# ---------------------------------------------------------------------------

class SourceWebsiteSnapshot(BaseModel):
    """Source website content extracted verbatim — ready for markdown formatting."""
    business_name: str = ""
    business_description: Optional[str] = None
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    website_url: Optional[str] = None

    navigation_items: List[NavItem] = Field(default_factory=list)
    hero_title: Optional[str] = None
    hero_subtitle: Optional[str] = None
    hero_description: Optional[str] = None
    hero_ctas: List[CallToAction] = Field(default_factory=list)
    hero_images: List[str] = Field(default_factory=list)

    section_order: List[str] = Field(default_factory=list)
    section_headings: Dict[str, str] = Field(default_factory=dict)
    section_subheadings: Dict[str, str] = Field(default_factory=dict)
    section_descriptions: Dict[str, str] = Field(default_factory=dict)

    services: List[ServiceCard] = Field(default_factory=list)
    products: List[ProductItem] = Field(default_factory=list)
    testimonials: List[Testimonial] = Field(default_factory=list)
    faqs: List[FAQ] = Field(default_factory=list)
    team: List[TeamMember] = Field(default_factory=list)
    company: Optional[CompanySection] = None
    trust_signals: List[str] = Field(default_factory=list)

    contact_emails: List[str] = Field(default_factory=list)
    contact_phones: List[str] = Field(default_factory=list)
    contact_address: Optional[str] = None
    contact_form_present: bool = False

    social_links: List[SocialLink] = Field(default_factory=list)
    footer: Optional[FooterInfo] = None

    images: List[ImageAsset] = Field(default_factory=list)
    section_image_map: Dict[str, List[str]] = Field(default_factory=dict)

    call_to_actions: List[CallToAction] = Field(default_factory=list)

    page_title: Optional[str] = None
    meta_description: Optional[str] = None

    @classmethod
    def from_profile(cls, profile: WebsiteProfile) -> SourceWebsiteSnapshot:
        biz: BusinessInfo = profile.business or BusinessInfo()
        hero: Optional[HeroInfo] = profile.hero_info
        wl: Optional[WebsiteLayout] = profile.website_layout
        nav_info: Optional[NavigationInfo] = profile.navigation_info
        contact: ContactInfo = profile.contact or ContactInfo()
        footer: Optional[FooterInfo] = wl.footer_info if wl else None
        seo = profile.seo

        section_order: List[str] = []
        section_headings: Dict[str, str] = {}
        section_subheadings: Dict[str, str] = {}
        section_descriptions: Dict[str, str] = {}
        section_image_map: Dict[str, List[str]] = {}

        if wl and wl.sections:
            for s in wl.sections:
                section_order.append(s.section_type)
                if s.heading:
                    section_headings[s.section_type] = s.heading
                if s.subheading:
                    section_subheadings[s.section_type] = s.subheading
                if s.description:
                    section_descriptions[s.section_type] = s.description
                if s.images:
                    section_image_map[s.section_type] = list(s.images)

        hero_images: List[str] = []
        if hero:
            if hero.hero_image:
                hero_images.append(hero.hero_image)
            if hero.background_image_url:
                hero_images.append(hero.background_image_url)

        hero_ctas: List[CallToAction] = []
        if hero and hero.ctas:
            seen = set()
            for c in hero.ctas:
                key = (c.text, c.url or "")
                if key not in seen:
                    seen.add(key)
                    hero_ctas.append(CallToAction(
                        text=c.text, url=c.url,
                        type=getattr(c, "type", None),
                        color=getattr(c, "color", None),
                    ))

        nav_items: List[NavItem] = []
        if nav_info:
            nav_items = nav_info.primary_nav_items or []

        trust_signals: List[str] = []
        if profile.trust_signals:
            for ts in profile.trust_signals:
                if ts.value:
                    trust_signals.append(ts.value)

        return cls(
            business_name=biz.name or "",
            business_description=biz.description,
            logo_url=biz.logo,
            favicon_url=biz.favicon,
            website_url=biz.website_url,
            navigation_items=nav_items,
            hero_title=hero.hero_title if hero else None,
            hero_subtitle=hero.hero_subtitle if hero else None,
            hero_description=hero.hero_description if hero else None,
            hero_ctas=hero_ctas,
            hero_images=hero_images,
            section_order=section_order,
            section_headings=section_headings,
            section_subheadings=section_subheadings,
            section_descriptions=section_descriptions,
            services=[s for s in (profile.services or []) if s.name],
            products=[p for p in (profile.products or []) if p.title],
            testimonials=profile.testimonials or [],
            faqs=profile.faqs or [],
            team=profile.team or [],
            company=profile.company,
            trust_signals=trust_signals,
            contact_emails=list(contact.emails or []),
            contact_phones=list(contact.phones or []),
            contact_address=contact.address,
            contact_form_present=contact.contact_form_present,
            social_links=profile.social_links or [],
            footer=footer,
            images=profile.images or [],
            section_image_map=section_image_map,
            call_to_actions=profile.call_to_actions or [],
            page_title=seo.page_title if seo else None,
            meta_description=seo.meta_description if seo else None,
        )


# ---------------------------------------------------------------------------
# Markdown formatter
# ---------------------------------------------------------------------------

def format_source_content(snapshot: SourceWebsiteSnapshot, manifest: Optional["AssetManifest"] = None) -> str:
    """Format the snapshot as a structured markdown document with strict
    instructions to preserve every piece of source content verbatim."""
    parts: List[str] = []

    # ── Header ───────────────────────────────────────────────────────── #
    parts.append(
        "# Source Website Content — USE VERBATIM\n\n"
        "Every item below was extracted from the ORIGINAL website. "
        "You MUST use this content exactly as written. "
        "Do not paraphrase, rewrite, summarize, or invent any content."
    )

    # ── Business ─────────────────────────────────────────────────────── #
    biz_lines: List[str] = []
    if snapshot.business_name:
        biz_lines.append(f"- **Business Name**: {snapshot.business_name}")
    if snapshot.business_description:
        biz_lines.append(f"- **Description**: {snapshot.business_description}")
    if snapshot.website_url:
        biz_lines.append(f"- **Website**: {snapshot.website_url}")
    if snapshot.logo_url:
        biz_lines.append(f"- **Logo URL**: {snapshot.logo_url}")
    if snapshot.favicon_url:
        biz_lines.append(f"- **Favicon URL**: {snapshot.favicon_url}")
    if biz_lines:
        parts.append("## Business\n\n" + "\n".join(biz_lines))

    # ── Navigation ──────────────────────────────────────────────────── #
    nav_lines: List[str] = []
    for item in snapshot.navigation_items:
        label = item.label or "?"
        url = item.url or ""
        nav_lines.append(f"- **{label}**: {url}")
        if item.dropdown_items:
            for child in item.dropdown_items:
                cl = child.label or "?"
                cu = child.url or ""
                nav_lines.append(f"  - {cl}: {cu}")
    if nav_lines:
        parts.append("## Navigation\n\n" + "\n".join(nav_lines))

    # ── Hero ────────────────────────────────────────────────────────── #
    hero_lines: List[str] = []
    if snapshot.hero_title:
        hero_lines.append(f"- **Heading**: {snapshot.hero_title}")
    if snapshot.hero_subtitle:
        hero_lines.append(f"- **Subheading**: {snapshot.hero_subtitle}")
    if snapshot.hero_description:
        hero_lines.append(f"- **Description**: {snapshot.hero_description}")
    for cta in snapshot.hero_ctas:
        hero_lines.append(f"- **CTA**: “{cta.text}” → {cta.url or '#'}")
    for img_url in snapshot.hero_images:
        hero_lines.append(f"- **Image**: {img_url}")
    if hero_lines:
        parts.append("## Hero Section\n\n" + "\n".join(hero_lines))

    # ── Section Order ───────────────────────────────────────────────── #
    if snapshot.section_order:
        parts.append(
            "## Page Section Order\n\n"
            + " → ".join(snapshot.section_order)
        )

    # ── Services ─────────────────────────────────────────────────────── #
    if snapshot.services:
        svc_parts: List[str] = []
        for svc in snapshot.services:
            svc_parts.append(f"### {svc.name}")
            if svc.description:
                svc_parts.append(f"\n{svc.description}")
            if svc.short_description and svc.short_description != svc.description:
                svc_parts.append(f"\n**Short description**: {svc.short_description}")
            if svc.full_description:
                svc_parts.append(f"\n**Full description**: {svc.full_description}")
            if svc.features:
                for f in svc.features:
                    svc_parts.append(f"\n- {f}")
            if svc.icon:
                svc_parts.append(f"\n- **Icon**: {svc.icon}")
            if svc.image:
                svc_parts.append(f"\n- **Image**: {svc.image}")
            if svc.source_url:
                svc_parts.append(f"\n- **Source**: {svc.source_url}")
            if svc.cta:
                svc_parts.append(f"\n- **CTA**: “{svc.cta.text}” → {svc.cta.url}")
            if svc.price:
                currency = svc.currency or "$"
                svc_parts.append(f"\n- **Price**: {currency}{svc.price}")
            svc_parts.append("")
        parts.append("## Services\n\n" + "\n".join(svc_parts))

    # ── Products ─────────────────────────────────────────────────────── #
    if snapshot.products:
        prod_parts: List[str] = []
        for p in snapshot.products:
            prod_parts.append(f"### {p.title}")
            if p.subtitle:
                prod_parts.append(f"\n**{p.subtitle}**")
            if p.short_description:
                prod_parts.append(f"\n{p.short_description}")
            if p.full_description:
                prod_parts.append(f"\n{p.full_description}")
            if p.image:
                prod_parts.append(f"\n- **Image**: {p.image}")
            if p.icon:
                prod_parts.append(f"\n- **Icon**: {p.icon}")
            if p.source_url:
                prod_parts.append(f"\n- **Source**: {p.source_url}")
            if p.cta:
                prod_parts.append(f"\n- **CTA**: “{p.cta.text}” → {p.cta.url}")
            if p.price:
                currency = p.currency or "$"
                prod_parts.append(f"\n- **Price**: {currency}{p.price}")
            if p.badge:
                prod_parts.append(f"\n- **Badge**: {p.badge}")
            prod_parts.append("")
        parts.append("## Products\n\n" + "\n".join(prod_parts))

    # ── Testimonials ───────────────────────────────────────────────── #
    if snapshot.testimonials:
        test_parts: List[str] = []
        for t in snapshot.testimonials:
            author = t.author_name or t.author or ""
            role = t.job_title or t.role or ""
            company = t.company_name or t.company or ""
            header = author
            if role and company:
                header += f", {role} at {company}"
            elif role:
                header += f", {role}"
            elif company:
                header += f", {company}"
            test_parts.append(f"### {header}" if header else "### Testimonial")
            test_parts.append(f"\n> “{t.content}”")
            if t.review_text and t.review_text != t.content:
                test_parts.append(f"\n{t.review_text}")
            if t.rating or t.star_count:
                stars = t.rating or t.star_count
                test_parts.append(f"\n- **Rating**: {'★' * stars}{'☆' * (5 - stars)} ({stars}/5)")
            if t.avatar_url or t.avatar:
                test_parts.append(f"\n- **Avatar**: {t.avatar_url or t.avatar}")
            if t.source_url:
                test_parts.append(f"\n- **Source**: {t.source_url}")
            if t.verified_badge:
                test_parts.append("\n- **Verified**: Yes")
            test_parts.append("")
        parts.append("## Testimonials\n\n" + "\n".join(test_parts))

    # ── FAQs ────────────────────────────────────────────────────────── #
    if snapshot.faqs:
        faq_parts: List[str] = []
        for faq in snapshot.faqs:
            faq_parts.append(f"### Q: {faq.question}")
            faq_parts.append(f"\nA: {faq.answer}")
            if faq.category:
                faq_parts.append(f"\n- **Category**: {faq.category}")
            faq_parts.append("")
        parts.append("## FAQs\n\n" + "\n".join(faq_parts))

    # ── Team ────────────────────────────────────────────────────────── #
    if snapshot.team:
        team_parts: List[str] = []
        for m in snapshot.team:
            name = m.full_name or m.name or ""
            title = m.job_title or m.role or ""
            bio = m.bio or ""
            header = name
            if title:
                header += f" — {title}"
            team_parts.append(f"### {header}")
            if bio:
                team_parts.append(f"\n{bio}")
            if m.photo_url or m.image:
                team_parts.append(f"\n- **Photo**: {m.photo_url or m.image}")
            if m.email:
                team_parts.append(f"\n- **Email**: {m.email}")
            if m.qualifications:
                for q in m.qualifications:
                    team_parts.append(f"\n- **Qualification**: {q}")
            if m.certifications:
                for c in m.certifications:
                    team_parts.append(f"\n- **Certification**: {c}")
            team_parts.append("")
        parts.append("## Team\n\n" + "\n".join(team_parts))

    # ── Company / About ───────────────────────────────────────────────── #
    if snapshot.company:
        co_lines: List[str] = []
        c = snapshot.company
        if c.section_title:
            co_lines.append(f"- **Section Title**: {c.section_title}")
        if c.section_type:
            co_lines.append(f"- **Section Type**: {c.section_type}")
        if c.description:
            co_lines.append(f"- **Description**: {c.description}")
        if c.mission:
            co_lines.append(f"- **Mission**: {c.mission}")
        if c.vision:
            co_lines.append(f"- **Vision**: {c.vision}")
        if c.core_values:
            for v in c.core_values:
                co_lines.append(f"- **Core Value**: {v}")
        if c.years_in_business:
            co_lines.append(f"- **Years in Business**: {c.years_in_business}")
        if c.company_size:
            co_lines.append(f"- **Company Size**: {c.company_size}")
        if c.business_type:
            co_lines.append(f"- **Business Type**: {c.business_type}")
        if c.target_audience:
            co_lines.append(f"- **Target Audience**: {c.target_audience}")
        if c.industries_served:
            for ind in c.industries_served:
                co_lines.append(f"- **Industry Served**: {ind}")
        if c.usp:
            co_lines.append(f"- **USP**: {c.usp}")
        if co_lines:
            parts.append("## Company / About\n\n" + "\n".join(co_lines))

    # ── Trust Signals ───────────────────────────────────────────────── #
    if snapshot.trust_signals:
        ts_lines: List[str] = []
        for ts in snapshot.trust_signals:
            ts_lines.append(f"- {ts}")
        parts.append("## Trust Signals\n\n" + "\n".join(ts_lines))

    # ── Contact ─────────────────────────────────────────────────────── #
    contact_lines: List[str] = []
    if snapshot.contact_emails:
        for e in snapshot.contact_emails:
            contact_lines.append(f"- **Email**: {e}")
    if snapshot.contact_phones:
        for p in snapshot.contact_phones:
            contact_lines.append(f"- **Phone**: {p}")
    if snapshot.contact_address:
        contact_lines.append(f"- **Address**: {snapshot.contact_address}")
    if snapshot.contact_form_present:
        contact_lines.append("- **Contact Form**: Present")
    if snapshot.social_links:
        for sl in snapshot.social_links:
            contact_lines.append(f"- **{sl.platform}**: {sl.url}")
    if contact_lines:
        parts.append("## Contact\n\n" + "\n".join(contact_lines))

    # ── Footer ──────────────────────────────────────────────────────── #
    if snapshot.footer:
        ft_lines: List[str] = []
        f = snapshot.footer
        if f.footer_description:
            ft_lines.append(f"- **Description**: {f.footer_description}")
        if f.footer_logo:
            ft_lines.append(f"- **Logo**: {f.footer_logo}")
        if f.copyright_text:
            ft_lines.append(f"- **Copyright**: {f.copyright_text}")
        if f.footer_links:
            for link in f.footer_links:
                ft_lines.append(f"- **Link**: {link.label or '?'} → {link.url or '#'}")
        if f.contact_info:
            ci = f.contact_info
            if ci.emails:
                for e in ci.emails:
                    ft_lines.append(f"- **Footer Email**: {e}")
            if ci.phones:
                for p in ci.phones:
                    ft_lines.append(f"- **Footer Phone**: {p}")
            if ci.address:
                ft_lines.append(f"- **Footer Address**: {ci.address}")
        if f.social_links:
            for sl in f.social_links:
                ft_lines.append(f"- **Footer {sl.platform}**: {sl.url}")
        if f.newsletter_signup:
            ft_lines.append("- **Newsletter**: Present")
            if f.newsletter_action_url:
                ft_lines.append(f"  - **Action URL**: {f.newsletter_action_url}")
        if ft_lines:
            parts.append("## Footer\n\n" + "\n".join(ft_lines))

    # ── Call to Actions ─────────────────────────────────────────────── #
    if snapshot.call_to_actions:
        cta_lines: List[str] = []
        for c in snapshot.call_to_actions:
            cta_lines.append(f"- **“{c.text}”** → {c.url or '#'}")
            if c.type:
                cta_lines[-1] += f" (type: {c.type})"
            if c.color:
                cta_lines[-1] += f" (color: {c.color})"
        parts.append("## Call to Actions\n\n" + "\n".join(cta_lines))

    # ── Section-Associated Images (from manifest) ──────────────────── #
    if manifest:
        section_items: Dict[str, List[AssetManifestItem]] = {}
        for item in manifest.items:
            sec = item.source_section or "unassigned"
            if sec not in section_items:
                section_items[sec] = []
            section_items[sec].append(item)

        for sec_name in sorted(section_items.keys()):
            items = section_items[sec_name]
            sec_lines: List[str] = []
            for item in items:
                line = f"- **URL**: {item.absolute_url}"
                if item.alt_text:
                    line += f"\n  - **Alt**: {item.alt_text}"
                if item.role:
                    line += f"\n  - **Role**: {item.role}"
                if item.related_item_name:
                    line += f"\n  - **Item**: {item.related_item_name}"
                if item.width and item.height:
                    line += f"\n  - **Dimensions**: {item.width}x{item.height}"
                if item.local_filename:
                    line += f"\n  - **Local File**: {item.local_filename}"
                sec_lines.append(line)
            if sec_lines:
                parts.append(f"## {sec_name.title()} Images\n\n" + "\n".join(sec_lines))

    # ── Image Inventory ─────────────────────────────────────────────── #
    if snapshot.images:
        img_lines: List[str] = []
        for img in snapshot.images:
            entry = f"- **URL**: {img.url}"
            if img.alt:
                entry += f"\n  - **Alt**: {img.alt}"
            if img.width and img.height:
                entry += f"\n  - **Dimensions**: {img.width}x{img.height}"
            if img.type:
                entry += f"\n  - **Type**: {img.type}"
            img_lines.append(entry)
        parts.append("## Image Inventory\n\n" + "\n".join(img_lines))

    # ── Complete Approved Asset Manifest ───────────────────────────── #
    if manifest and manifest.items:
        asset_lines: List[str] = []
        for i, item in enumerate(manifest.items, 1):
            line = f"{i}. **URL**: {item.absolute_url}"
            if item.role:
                line += f" | **Role**: {item.role}"
            if item.source_section:
                line += f" | **Section**: {item.source_section}"
            if item.related_item_name:
                line += f" | **Item**: {item.related_item_name}"
            if item.local_filename:
                line += f" | **Local**: {item.local_filename}"
            if item.alt_text:
                line += f" | **Alt**: {item.alt_text[:80]}"
            if item.download_status:
                line += f" | **Status**: {item.download_status}"
            asset_lines.append(line)
        parts.append("## Approved Asset Manifest\n\n" + "\n".join(asset_lines))

    # ── SEO ─────────────────────────────────────────────────────────── #
    seo_lines: List[str] = []
    if snapshot.page_title:
        seo_lines.append(f"- **Page Title**: {snapshot.page_title}")
    if snapshot.meta_description:
        seo_lines.append(f"- **Meta Description**: {snapshot.meta_description}")
    if seo_lines:
        parts.append("## SEO Metadata\n\n" + "\n".join(seo_lines))

    # ── Strict instructions ─────────────────────────────────────────── #
    parts.append(
        "\n---\n"
        "## STRICT RULES — MUST FOLLOW\n\n"
        "- REDESIGN the source website above. Use the EXACT content - never paraphrase, rewrite, or improve business claims.\n"
        "- Use ONLY approved source images listed in the Approved Asset Manifest section above.\n"
        "- Never invent missing content. If something is not listed, omit it.\n"
        "- Never use \"Lorem Ipsum\" or placeholder text.\n"
        "- Never create \"Service 1\", \"Service 2\", or similar dummy entries.\n"
        "- Never add LeadForge branding, logos, or watermarks.\n"
        "- Only use image URLs listed in the Section Images, Image Inventory, or Approved Asset Manifest above.\n"
        "- Never invent or generate new images.\n"
        "- Never substitute stock photography, AI-generated images, or generic placeholders.\n"
        "- Never reference a local asset file unless it exists in the Approved Asset Manifest.\n"
        "- Preserve all navigation labels, URLs, and hierarchy exactly as listed.\n"
        "- Preserve all service names, descriptions, features, and prices exactly.\n"
        "- Preserve all testimonial quotes, authors, ratings, and avatars exactly.\n"
        "- Preserve all FAQ questions and answers exactly.\n"
        "- Preserve all contact details (email, phone, address) exactly.\n"
        "- Preserve all social media links exactly.\n"
        "- Preserve all footer content exactly.\n"
        "- Do not add any section that was not present in the original page.\n"
        "- If an image URL is listed, use it directly as the img src.\n"
        "- Do not prefix, suffix, or modify any image URL.\n"
        "- If a local file path is listed for an asset, use it in preference to the remote URL.\n"
        "- Do not create new image paths, filenames, or asset locations."
    )

    return "\n\n".join(parts)
