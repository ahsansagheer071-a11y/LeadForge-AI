import uuid
import time
import asyncio
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ValidationException, ServiceUnavailableException
from app.core.logging import logger
from app.models.user import User
from app.repositories.lead import lead_repository
from app.repositories.audit import audit_repository
from app.repositories.screenshot import screenshot_repository
from app.services.ai.factory import ai_factory


class AuditEngineService:
    """
    Orchestrates the AI Audit Engine process: loads lead info, raw web data,
    screenshots, invokes the provider-agnostic AI provider, and updates the Audit.
    """

    async def generate_audit(
        self,
        db: AsyncSession,
        *,
        lead_id: uuid.UUID,
        user: User,
        provider: str = "groq",
    ) -> Dict[str, Any]:
        logger.info("AI Audit initiated | lead_id=%s | provider=%s", lead_id, provider)
        t_start = time.perf_counter()

        # 1. Load lead, audit, and screenshot data concurrently
        lead, audit_record, screenshot_record = await asyncio.gather(
            lead_repository.get(db, id=lead_id),
            audit_repository.get_by_lead_id(db, lead_id=lead_id),
            screenshot_repository.get_by_lead_id(db, lead_id=lead_id),
        )

        t_load = time.perf_counter()
        logger.info("DB load phase | lead_id=%s | took=%.2fs", lead_id, t_load - t_start)

        if not lead or lead.user_id != user.id:
            raise NotFoundException(f"Lead with id '{lead_id}' not found.")

        if not audit_record:
            raise ValidationException("Please analyze the website using Website Analyzer first.")

        # 2. Build lead info
        lead_info = {
            "name": lead.name,
            "industry": lead.industry,
            "city": lead.city,
            "country": lead.country,
            "rating": lead.rating,
            "reviews_count": lead.reviews_count,
        }

        # 3. Build screenshot URLs
        screenshot_urls = {}
        if screenshot_record:
            screenshot_urls = {
                "desktop_url": screenshot_record.desktop_cloudinary_url,
                "mobile_url": screenshot_record.mobile_cloudinary_url,
                "full_page_url": screenshot_record.full_page_cloudinary_url,
            }

        # 4. Build website analysis dict
        website_analysis = {
            "website_title": audit_record.website_title,
            "meta_description": audit_record.meta_description,
            "emails": audit_record.emails,
            "phone_numbers": audit_record.phone_numbers,
            "contact_form_present": audit_record.contact_form_present,
            "social_links": audit_record.social_links,
            "technologies": audit_record.technologies,
            "ssl_status": audit_record.ssl_status,
            "images": audit_record.images,
            "navigation_structure": audit_record.navigation_structure,
            "cta_buttons": audit_record.cta_buttons,
            "testimonials_present": audit_record.testimonials_present,
            "faq_present": audit_record.faq_present,
            "website_language": audit_record.website_language,
            "https_enabled": audit_record.https_enabled,
            "http_status_code": audit_record.http_status_code,
            "h1_count": audit_record.h1_count,
            "h2_count": audit_record.h2_count,
            "total_paragraphs": audit_record.total_paragraphs,
            "total_images": audit_record.total_images,
            "total_forms": audit_record.total_forms,
            "contact_page_exists": audit_record.contact_page_exists,
            "about_page_exists": audit_record.about_page_exists,
            "social_facebook": audit_record.social_facebook,
            "social_instagram": audit_record.social_instagram,
            "social_linkedin": audit_record.social_linkedin,
            "social_twitter": audit_record.social_twitter,
            "social_youtube": audit_record.social_youtube,
            "missing_meta_description": audit_record.missing_meta_description,
            "missing_h1": audit_record.missing_h1,
            "missing_title": audit_record.missing_title,
            "html_size_kb": audit_record.html_size_kb,
            "response_time_ms": audit_record.response_time_ms,
        }

        # 5. Invoke AI Provider with timeout guard
        ai_provider = ai_factory.get_provider(provider)

        t_ai_start = time.perf_counter()
        try:
            ai_result = await asyncio.wait_for(
                ai_provider.audit_website(lead_info, website_analysis, screenshot_urls),
                timeout=120.0,
            )
        except asyncio.TimeoutError:
            logger.error("AI audit timed out | lead_id=%s | provider=%s", lead_id, provider)
            raise ServiceUnavailableException(
                f"AI audit timed out after 120s for lead '{lead_id}'."
            )
        t_ai_end = time.perf_counter()
        logger.info(
            "AI provider phase | lead_id=%s | took=%.2fs",
            lead_id,
            t_ai_end - t_ai_start,
        )

        # 6. Update Audit Record
        update_data = {
            "executive_summary": ai_result.get("Business Summary"),
            "weaknesses": ai_result.get("Top Weaknesses"),
            "verdict": ai_result.get("Overall Summary"),
        }
        await audit_repository.update(db, db_obj=audit_record, obj_in=update_data)

        t_total = time.perf_counter()
        logger.info(
            "AI Audit completed | lead_id=%s | total=%.2fs",
            lead_id,
            t_total - t_start,
        )
        return ai_result


audit_engine_service = AuditEngineService()
