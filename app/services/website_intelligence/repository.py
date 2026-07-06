import uuid
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.website_intelligence.models import WebsiteIntelligence
from app.services.website_intelligence.schemas import WebsiteProfile


class WebsiteIntelligenceRepository:
    """
    Repository for WebsiteIntelligence CRUD operations.
    No business logic — only database access.
    """

    def __init__(self) -> None:
        self.model = WebsiteIntelligence

    async def create(
        self,
        db: AsyncSession,
        *,
        lead_id: uuid.UUID,
        profile: WebsiteProfile,
    ) -> WebsiteIntelligence:
        profile_data = profile.model_dump()
        mapped = self._map_profile_to_columns(lead_id, profile_data)
        db_obj = self.model(**mapped)
        db.add(db_obj)
        await db.flush()
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        lead_id: uuid.UUID,
        profile: WebsiteProfile,
    ) -> Optional[WebsiteIntelligence]:
        db_obj = await self.get_by_lead(db, lead_id=lead_id)
        if not db_obj:
            return None
        profile_data = profile.model_dump()
        mapped = self._map_profile_to_columns(lead_id, profile_data)
        for field, value in mapped.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        await db.flush()
        return db_obj

    async def get_by_lead(
        self,
        db: AsyncSession,
        *,
        lead_id: uuid.UUID,
    ) -> Optional[WebsiteIntelligence]:
        result = await db.execute(
            select(self.model).filter(self.model.lead_id == lead_id)
        )
        return result.scalars().first()

    async def delete(
        self,
        db: AsyncSession,
        *,
        lead_id: uuid.UUID,
    ) -> bool:
        db_obj = await self.get_by_lead(db, lead_id=lead_id)
        if not db_obj:
            return False
        await db.delete(db_obj)
        await db.flush()
        return True

    async def exists(
        self,
        db: AsyncSession,
        *,
        lead_id: uuid.UUID,
    ) -> bool:
        result = await db.execute(
            select(self.model.id).filter(self.model.lead_id == lead_id).limit(1)
        )
        return result.scalars().first() is not None

    def _map_profile_to_columns(
        self,
        lead_id: uuid.UUID,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        business = data.get("business", {}) or {}
        brand = data.get("brand", {}) or {}
        seo = data.get("seo", {}) or {}
        colors = data.get("colors", {}) or {}
        typography = data.get("typography", {}) or {}
        contact = data.get("contact", {}) or {}
        navigation = data.get("navigation", []) or []
        hero = data.get("hero", {}) or {}
        services = data.get("services", []) or []
        products = data.get("products", []) or []
        images = data.get("images", []) or []
        testimonials = data.get("testimonials", []) or []
        faqs = data.get("faqs", []) or []
        team = data.get("team", []) or []
        blog_links = data.get("blog_links", []) or []
        social_links = data.get("social_links", []) or []
        call_to_actions = data.get("call_to_actions", []) or []
        statistics = data.get("statistics", {}) or {}

        return {
            "lead_id": lead_id,
            "business_name": business.get("name", ""),
            "business_legal_name": business.get("legal_name"),
            "business_category": business.get("category"),
            "business_industry": business.get("industry"),
            "business_description": business.get("description"),
            "logo_url": business.get("logo"),
            "favicon_url": business.get("favicon"),
            "website_url": business.get("website_url"),
            "phone": business.get("phone"),
            "email": business.get("email"),
            "address": business.get("address"),
            "city": business.get("city"),
            "country": business.get("country"),
            "google_maps_url": business.get("google_maps_url"),
            "opening_hours": business.get("opening_hours"),
            "founded_year": business.get("founded_year"),
            "employee_count": business.get("employee_count"),
            "social_links": business.get("social_links") or None,
            "website_summary": data.get("website_summary"),
            "brand_tagline": brand.get("tagline"),
            "brand_voice": brand.get("brand_voice"),
            "brand_unique_selling_points": brand.get("unique_selling_points") or None,
            "target_audience": brand.get("target_audience"),
            "logo_info_url": logo.get("logo_url") if (logo := brand.get("logo_info")) else None,
            "logo_info_format": logo.get("format") if (logo := brand.get("logo_info")) else None,
            "logo_info_has_transparency": logo.get("has_transparent_background") if (logo := brand.get("logo_info")) else None,
            "logo_info_width": logo.get("estimated_width") if (logo := brand.get("logo_info")) else None,
            "logo_info_height": logo.get("estimated_height") if (logo := brand.get("logo_info")) else None,
            "logo_info_dominant_colors": logo.get("dominant_colors") or None if (logo := brand.get("logo_info")) else None,
            "logo_info_position": logo.get("position") if (logo := brand.get("logo_info")) else None,
            "logo_info_retina_quality": logo.get("is_retina_quality", False) if (logo := brand.get("logo_info")) else False,
            "logo_info_is_favicon_fallback": logo.get("is_favicon_fallback", False) if (logo := brand.get("logo_info")) else False,
            "color_primary": colors.get("primary"),
            "color_secondary": colors.get("secondary"),
            "color_accent": colors.get("accent"),
            "color_background": colors.get("background"),
            "color_text": colors.get("text"),
            "color_surface": colors.get("surface"),
            "color_heading": colors.get("heading"),
            "color_border": colors.get("border"),
            "color_muted": colors.get("muted"),
            "color_dark": colors.get("dark"),
            "color_light": colors.get("light"),
            "color_success": colors.get("success"),
            "color_warning": colors.get("warning"),
            "color_danger": colors.get("danger"),
            "color_info": colors.get("info"),
            "color_computed_data": colors.get("computed_colors") or None,
            "color_contrast_ratios": colors.get("contrast_ratios") or None,
            "color_wcag_compliance": colors.get("wcag_compliance") or None,
            "color_poor_combinations": colors.get("poor_combinations") or None,
            "color_accessibility_score": colors.get("accessibility_score"),
            "fonts": typography.get("fonts") or None,
            "heading_h1": typography.get("heading_h1"),
            "heading_h2": typography.get("heading_h2"),
            "heading_h3": typography.get("heading_h3"),
            "body_font": typography.get("body"),
            "typography_primary_font": ti.get("primary_font") if (ti := brand.get("typography_info")) else None,
            "typography_heading_font": ti.get("heading_font") if (ti := brand.get("typography_info")) else None,
            "typography_secondary_font": ti.get("secondary_font") if (ti := brand.get("typography_info")) else None,
            "typography_fallback_stack": ti.get("fallback_stack") or None if (ti := brand.get("typography_info")) else None,
            "typography_is_google_font": ti.get("is_google_font", False) if (ti := brand.get("typography_info")) else False,
            "typography_is_system_font": ti.get("is_system_font", False) if (ti := brand.get("typography_info")) else False,
            "typography_weights_used": ti.get("weights_used") or None if (ti := brand.get("typography_info")) else None,
            "typography_hierarchy": ti.get("hierarchy") or None if (ti := brand.get("typography_info")) else None,
            "design_language_name": dl.get("design_language") if (dl := brand.get("design_language")) else None,
            "design_language_confidence": dl.get("confidence_score") if (dl := brand.get("design_language")) else None,
            "design_language_all_scores": dl.get("all_scores") or None if (dl := brand.get("design_language")) else None,
            "brand_personality_traits": bp.get("personality_traits") or None if (bp := brand.get("brand_personality")) else None,
            "brand_personality_scores": bp.get("confidence_percentages") or None if (bp := brand.get("brand_personality")) else None,
            "consistency_overall_score": cr.get("overall_consistency_score") if (cr := brand.get("consistency_report")) else None,
            "consistency_color_score": cr.get("color_consistency") if (cr := brand.get("consistency_report")) else None,
            "consistency_spacing_score": cr.get("spacing_consistency") if (cr := brand.get("consistency_report")) else None,
            "consistency_typography_score": cr.get("typography_consistency") if (cr := brand.get("consistency_report")) else None,
            "consistency_button_score": cr.get("button_consistency") if (cr := brand.get("consistency_report")) else None,
            "consistency_card_score": cr.get("card_consistency") if (cr := brand.get("consistency_report")) else None,
            "consistency_border_radius_score": cr.get("border_radius_consistency") if (cr := brand.get("consistency_report")) else None,
            "consistency_shadow_score": cr.get("shadow_consistency") if (cr := brand.get("consistency_report")) else None,
            "consistency_component_counts": cr.get("component_counts") or None if (cr := brand.get("consistency_report")) else None,
            "consistency_skipped_components": cr.get("skipped_components") or None if (cr := brand.get("consistency_report")) else None,
            "component_styles": cs.get("component_styles") or None if (cs := brand.get("component_styles")) else None,
            "navigation_items": navigation or None,
            "navigation_logo": None,
            "is_sticky_nav": nav_info.get("is_sticky", False) if (nav_info := data.get("navigation_info")) else False,
            "nav_primary_items": nav_info.get("primary_nav_items") or None if (nav_info := data.get("navigation_info")) else None,
            "nav_secondary_items": nav_info.get("secondary_nav_items") or None if (nav_info := data.get("navigation_info")) else None,
            "nav_footer_items": nav_info.get("footer_nav_items") or None if (nav_info := data.get("navigation_info")) else None,
            "nav_depth": nav_info.get("navigation_depth") if (nav_info := data.get("navigation_info")) else None,
            "hero_title": hero.get("title"),
            "hero_subtitle": hero.get("subtitle"),
            "hero_cta_buttons": hero.get("cta_buttons") or None,
            "hero_background_image": hero.get("background_image"),
            "hero_description": hi.get("hero_description") if (hi := data.get("hero_info")) else None,
            "hero_image": hi.get("hero_image") if (hi := data.get("hero_info")) else None,
            "hero_primary_cta": hi.get("primary_cta") if (hi := data.get("hero_info")) else None,
            "hero_secondary_cta": hi.get("secondary_cta") if (hi := data.get("hero_info")) else None,
            "hero_background_image_url": hi.get("background_image_url") if (hi := data.get("hero_info")) else None,
            "hero_background_color": hi.get("background_color") if (hi := data.get("hero_info")) else None,
            "hero_layout": hi.get("hero_layout") if (hi := data.get("hero_info")) else None,
            "hero_alignment": hi.get("hero_alignment") if (hi := data.get("hero_info")) else None,
            "hero_height": hi.get("hero_height") if (hi := data.get("hero_info")) else None,
            "is_fallback_detection": hi.get("is_fallback_detection", False) if (hi := data.get("hero_info")) else False,
            "sections": data.get("website_layout", {}).get("sections") or None,
            "ctas": data.get("website_layout", {}).get("ctas") or None,
            "footer_logo": fi.get("footer_logo") if (fi := data.get("website_layout", {}).get("footer_info")) else None,
            "footer_description": fi.get("footer_description") if (fi := data.get("website_layout", {}).get("footer_info")) else None,
            "footer_links": fi.get("footer_links") or None if (fi := data.get("website_layout", {}).get("footer_info")) else None,
            "footer_contact_emails": fi.get("contact_info", {}).get("emails") or None if (fi := data.get("website_layout", {}).get("footer_info")) else None,
            "footer_contact_phones": fi.get("contact_info", {}).get("phones") or None if (fi := data.get("website_layout", {}).get("footer_info")) else None,
            "footer_contact_address": fi.get("contact_info", {}).get("address") if (fi := data.get("website_layout", {}).get("footer_info")) else None,
            "footer_social_links": fi.get("social_links") or None if (fi := data.get("website_layout", {}).get("footer_info")) else None,
            "footer_copyright": fi.get("copyright_text") if (fi := data.get("website_layout", {}).get("footer_info")) else None,
            "footer_newsletter_signup": fi.get("newsletter_signup", False) if (fi := data.get("website_layout", {}).get("footer_info")) else False,
            "footer_newsletter_action": fi.get("newsletter_action_url") if (fi := data.get("website_layout", {}).get("footer_info")) else None,
            "footer_is_fallback": fi.get("is_fallback_detection", False) if (fi := data.get("website_layout", {}).get("footer_info")) else False,
            "services": services or None,
            "products": products or None,
            "contact_emails": contact.get("emails") or None,
            "contact_phones": contact.get("phones") or None,
            "contact_address": contact.get("address"),
            "contact_form_present": contact.get("contact_form_present", False),
            "contact_form_fields": contact.get("contact_form_fields") or None,
            "contact_map_coordinates": contact.get("map_coordinates") or None,
            "images": images or None,
            "testimonials": testimonials or None,
            "faqs": faqs or None,
            "team_members": team or None,
            "company_info": data.get("company"),
            "trust_signals": data.get("trust_signals") or None,
            "statistics": statistics or None,
            "blog_links": blog_links or None,
            "social_links_present": social_links or None,
            "seo_page_title": seo.get("page_title"),
            "seo_meta_description": seo.get("meta_description"),
            "seo_focus_keywords": seo.get("focus_keywords") or None,
            "seo_missing_meta_description": seo.get("missing_meta_description", False),
            "seo_missing_title": seo.get("missing_title", False),
            "seo_missing_h1": seo.get("missing_h1", False),
            "seo_https_enabled": seo.get("https_enabled", False),
            "seo_ssl_status": seo.get("ssl_status", False),
            "call_to_actions": call_to_actions or None,
            "quality_metrics": data.get("quality_metrics") or None,
            "website_blueprint": data.get("blueprint") or None,
            "raw_html_size_kb": data.get("raw_html_size_kb"),
            "extraction_timestamp": data.get("extraction_timestamp"),
        }


website_intelligence_repository = WebsiteIntelligenceRepository()