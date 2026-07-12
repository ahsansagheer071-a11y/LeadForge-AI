"""ContentExtractor — pulls structured content from WebsiteProfile and
builds focused section prompts for multi-call generation.

Instead of truncating a 142KB markdown blob to 6000 chars, this extracts
every meaningful item (product, service, testimonial, FAQ, etc.) from the
structured WebsiteProfile and formats it compactly for each section call.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional

from app.services.website_intelligence.schemas import WebsiteProfile

logger = logging.getLogger(__name__)


@dataclass
class ContentSection:
    name: str
    prompt_text: str
    item_count: int = 0


@dataclass
class ContentManifest:
    hero: Optional[ContentSection] = None
    about: Optional[ContentSection] = None
    products: Optional[ContentSection] = None
    services: Optional[ContentSection] = None
    testimonials: Optional[ContentSection] = None
    faqs: Optional[ContentSection] = None
    contact: Optional[ContentSection] = None
    footer: Optional[ContentSection] = None
    total_items: int = 0

    def sections(self) -> List[ContentSection]:
        return [s for s in [self.hero, self.about, self.products,
                            self.services, self.testimonials, self.faqs,
                            self.contact, self.footer] if s is not None]


def _clean(text: Optional[str], max_len: int = 300) -> str:
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) > max_len:
        text = text[:max_len].rsplit(' ', 1)[0] + "..."
    return text


class ContentExtractor:
    """Extracts structured content from WebsiteProfile for section-by-section generation."""

    def __init__(self, profile: WebsiteProfile):
        self.profile = profile

    def extract(self) -> ContentManifest:
        manifest = ContentManifest()
        manifest.hero = self._extract_hero()
        manifest.about = self._extract_about()
        manifest.products = self._extract_products()
        manifest.services = self._extract_services()
        manifest.testimonials = self._extract_testimonials()
        manifest.faqs = self._extract_faqs()
        manifest.contact = self._extract_contact()
        manifest.footer = self._extract_footer()
        manifest.total_items = sum(s.item_count for s in manifest.sections())
        logger.info(
            "ContentExtractor: %d sections, %d total items",
            len(manifest.sections()), manifest.total_items,
        )
        return manifest

    def _extract_hero(self) -> ContentSection:
        lines = []
        count = 0

        biz = self.profile.business
        if biz.name:
            lines.append(f"Business Name: {biz.name}")
            count += 1
        if biz.description:
            lines.append(f"Description: {_clean(biz.description, 500)}")
            count += 1
        if biz.category:
            lines.append(f"Category: {biz.category}")
        if biz.industry:
            lines.append(f"Industry: {biz.industry}")

        brand = self.profile.brand
        if brand.tagline:
            lines.append(f"Tagline: {brand.tagline}")
            count += 1

        hero = self.profile.hero_info or self.profile.hero
        if hero:
            for attr in ['hero_title', 'title']:
                val = getattr(hero, attr, None)
                if val:
                    lines.append(f"Hero Title: {val}")
                    count += 1
                    break
            for attr in ['hero_subtitle', 'subtitle']:
                val = getattr(hero, attr, None)
                if val:
                    lines.append(f"Hero Subtitle: {_clean(val, 200)}")
                    count += 1
                    break
            for attr in ['hero_description', 'description']:
                val = getattr(hero, attr, None)
                if val:
                    lines.append(f"Hero Description: {_clean(val, 300)}")
                    count += 1
                    break

            ctas = []
            for attr in ['ctas', 'cta_buttons']:
                raw = getattr(hero, attr, None) or []
                if raw:
                    ctas = raw
                    break
            if not ctas and hasattr(hero, 'primary_cta') and hero.primary_cta:
                ctas = [hero.primary_cta]
            for cta in ctas[:3]:
                text = cta.get('text', '') if isinstance(cta, dict) else getattr(cta, 'text', '')
                url = cta.get('url', '') if isinstance(cta, dict) else getattr(cta, 'url', '')
                if text:
                    lines.append(f"CTA: {text} -> {url}")
                    count += 1

        if hasattr(biz, 'logo') and biz.logo:
            lines.append(f"Logo: {biz.logo}")
        if hasattr(biz, 'favicon') and biz.favicon:
            lines.append(f"Favicon: {biz.favicon}")

        hero_img = None
        if self.profile.hero_info and self.profile.hero_info.hero_image:
            hero_img = self.profile.hero_info.hero_image
        elif self.profile.hero and self.profile.hero.background_image:
            hero_img = self.profile.hero.background_image
        if hero_img:
            lines.append(f"Hero Image: {hero_img}")
            count += 1

        return ContentSection(
            name="hero",
            prompt_text="\n".join(lines) if lines else "No hero content available",
            item_count=count,
        )

    def _extract_about(self) -> ContentSection:
        lines = []
        count = 0

        biz = self.profile.business
        if biz.description:
            lines.append(f"Business: {_clean(biz.description, 500)}")
            count += 1

        company = self.profile.company
        if company:
            if company.mission:
                lines.append(f"Mission: {_clean(company.mission, 300)}")
                count += 1
            if company.vision:
                lines.append(f"Vision: {_clean(company.vision, 300)}")
                count += 1
            if company.core_values:
                lines.append(f"Core Values: {', '.join(company.core_values[:10])}")
                count += 1
            if company.years_in_business:
                lines.append(f"Years in Business: {company.years_in_business}")
            if company.company_size:
                lines.append(f"Company Size: {company.company_size}")
            if company.usp:
                lines.append(f"USP: {_clean(company.usp, 300)}")
                count += 1
            if company.target_audience:
                lines.append(f"Target Audience: {_clean(company.target_audience, 200)}")
            if company.industries_served:
                lines.append(f"Industries: {', '.join(company.industries_served[:5])}")

        brand = self.profile.brand
        if brand.brand_voice:
            lines.append(f"Brand Voice: {_clean(brand.brand_voice, 200)}")
        if brand.target_audience:
            lines.append(f"Target Audience: {_clean(brand.target_audience, 200)}")
        if brand.unique_selling_points:
            for usp in brand.unique_selling_points[:5]:
                lines.append(f"USP: {usp}")
                count += 1

        team = self.profile.team
        if team:
            lines.append(f"Team Members: {len(team)}")
            for member in team[:8]:
                role = member.role or member.job_title or ""
                name = member.full_name or member.name
                lines.append(f"  - {name}, {role}")
            count += min(len(team), 8)

        return ContentSection(
            name="about",
            prompt_text="\n".join(lines) if lines else "No about content available",
            item_count=count,
        )

    def _extract_products(self) -> ContentSection:
        products = self.profile.products or []
        if not products:
            return ContentSection(name="products", prompt_text="No products available", item_count=0)

        lines = [f"ALL PRODUCTS ({len(products)} total):"]
        for i, p in enumerate(products, 1):
            title = p.title or p.subtitle or f"Product {i}"
            parts = [f"{i}. \"{title}\""]
            if p.short_description:
                parts.append(f"   {_clean(p.short_description, 150)}")
            elif p.full_description:
                parts.append(f"   {_clean(p.full_description, 150)}")
            if p.price:
                parts.append(f"   Price: {p.price}" + (f" {p.currency}" if p.currency else ""))
            if p.category:
                parts.append(f"   Category: {p.category}")
            if p.badge:
                parts.append(f"   Badge: {p.badge}")
            if p.image:
                parts.append(f"   Image: {p.image}")
            elif p.icon:
                parts.append(f"   Icon: {p.icon}")
            lines.append("\n".join(parts))

        return ContentSection(
            name="products",
            prompt_text="\n".join(lines),
            item_count=len(products),
        )

    def _extract_services(self) -> ContentSection:
        services = self.profile.services or []
        if not services:
            return ContentSection(name="services", prompt_text="No services available", item_count=0)

        lines = [f"ALL SERVICES ({len(services)} total):"]
        for i, s in enumerate(services, 1):
            name = s.name or f"Service {i}"
            parts = [f"{i}. \"{name}\""]
            if s.description:
                parts.append(f"   {_clean(s.description, 150)}")
            elif s.short_description:
                parts.append(f"   {_clean(s.short_description, 150)}")
            elif s.full_description:
                parts.append(f"   {_clean(s.full_description, 150)}")
            if s.price:
                parts.append(f"   Price: {s.price}")
            if s.category:
                parts.append(f"   Category: {s.category}")
            if s.features:
                parts.append(f"   Features: {', '.join(s.features[:5])}")
            if s.image:
                parts.append(f"   Image: {s.image}")
            elif s.icon:
                parts.append(f"   Icon: {s.icon}")
            lines.append("\n".join(parts))

        return ContentSection(
            name="services",
            prompt_text="\n".join(lines),
            item_count=len(services),
        )

    def _extract_testimonials(self) -> ContentSection:
        testimonials = self.profile.testimonials or []
        if not testimonials:
            return ContentSection(name="testimonials", prompt_text="No testimonials available", item_count=0)

        lines = [f"ALL TESTIMONIALS ({len(testimonials)} total):"]
        for i, t in enumerate(testimonials, 1):
            author = t.author or t.author_name or "Anonymous"
            company = t.company or t.company_name or ""
            role = t.role or t.job_title or ""
            text = t.content or t.review_text or ""
            rating = t.rating or t.star_count
            parts = [f"{i}. Author: {author}"]
            if company:
                parts.append(f"   Company: {company}")
            if role:
                parts.append(f"   Role: {role}")
            if text:
                parts.append(f"   Text: {_clean(text, 200)}")
            if rating:
                parts.append(f"   Rating: {rating}/5")
            lines.append("\n".join(parts))

        return ContentSection(
            name="testimonials",
            prompt_text="\n".join(lines),
            item_count=len(testimonials),
        )

    def _extract_faqs(self) -> ContentSection:
        faqs = self.profile.faqs or []
        if not faqs:
            return ContentSection(name="faqs", prompt_text="No FAQs available", item_count=0)

        lines = [f"ALL FAQs ({len(faqs)} total):"]
        for i, faq in enumerate(faqs, 1):
            lines.append(f"{i}. Q: {faq.question}")
            lines.append(f"   A: {_clean(faq.answer, 250)}")

        return ContentSection(
            name="faqs",
            prompt_text="\n".join(lines),
            item_count=len(faqs),
        )

    def _extract_contact(self) -> ContentSection:
        lines = []
        count = 0

        contact = self.profile.contact
        if contact:
            if contact.emails:
                for email in contact.emails:
                    lines.append(f"Email: {email}")
                    count += 1
            if contact.phones:
                for phone in contact.phones:
                    lines.append(f"Phone: {phone}")
                    count += 1
            if contact.address:
                lines.append(f"Address: {contact.address}")
                count += 1
            if hasattr(contact, 'map_coordinates') and contact.map_coordinates:
                coords = contact.map_coordinates
                lines.append(f"Map: lat={coords.get('lat', '')}, lng={coords.get('lng', '')}")

        biz = self.profile.business
        if biz.email and biz.email not in (contact.emails or []):
            lines.append(f"Business Email: {biz.email}")
            count += 1
        if biz.phone and biz.phone not in (contact.phones or []):
            lines.append(f"Business Phone: {biz.phone}")
            count += 1
        if biz.address and biz.address != contact.address:
            lines.append(f"Business Address: {biz.address}")
            count += 1
        if biz.opening_hours:
            lines.append(f"Hours: {biz.opening_hours}")
        if biz.google_maps_url:
            lines.append(f"Google Maps: {biz.google_maps_url}")

        social = self.profile.social_links or []
        if biz.social_links:
            social = list(set(social + biz.social_links))
        for link in social[:10]:
            platform = link.platform if hasattr(link, 'platform') else str(link)
            url = link.url if hasattr(link, 'url') else ""
            lines.append(f"Social [{platform}]: {url}")
            count += 1

        return ContentSection(
            name="contact",
            prompt_text="\n".join(lines) if lines else "No contact information available",
            item_count=count,
        )

    def _extract_footer(self) -> ContentSection:
        lines = []
        count = 0

        biz = self.profile.business
        nav = self.profile.navigation_info
        if nav and nav.footer_nav_items:
            lines.append("Footer Navigation:")
            for item in nav.footer_nav_items[:10]:
                lines.append(f"  - {item.label}: {item.url}")
            count += len(nav.footer_nav_items[:10])

        social = self.profile.social_links or biz.social_links or []
        if social:
            lines.append(f"Social Links: {len(social)}")
            count += min(len(social), 5)

        if hasattr(self.profile, 'website_layout') and self.profile.website_layout:
            layout = self.profile.website_layout
            if layout.footer_info:
                fi = layout.footer_info
                if fi.copyright_text:
                    lines.append(f"Copyright: {fi.copyright_text}")
                if fi.footer_description:
                    lines.append(f"Footer Description: {_clean(fi.footer_description, 200)}")

        return ContentSection(
            name="footer",
            prompt_text="\n".join(lines) if lines else "No footer content available",
            item_count=count,
        )
