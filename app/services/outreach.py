import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import NotFoundException, ValidationException, ServiceUnavailableException
from app.core.logging import logger
from app.models.user import User
from app.repositories.lead import lead_repository
from app.repositories.audit import audit_repository
from app.repositories.lead_score import lead_score_repository
from app.repositories.outreach import outreach_repository
from app.repositories.generated_website import generated_website_repository
from app.schemas.outreach import OutreachCreate, OutreachResponse
from app.services.ai.factory import ai_factory
from app.services.ai.chain import run_chain


class OutreachService:
    async def generate_outreach(
        self,
        db: AsyncSession,
        *,
        lead_id: uuid.UUID,
        user: User,
        provider: str = "groq"
    ) -> OutreachResponse:
        logger.info("Outreach generation initiated | lead_id=%s | provider=%s", lead_id, provider)

        lead = await lead_repository.get(db, id=lead_id)
        if not lead or lead.user_id != user.id:
            raise NotFoundException(f"Lead with id '{lead_id}' not found.")

        audit_record = await audit_repository.get_by_lead_id(db, lead_id=lead_id)
        if not audit_record:
            raise ValidationException("Please complete Website Analysis and AI Audit first.")

        if not audit_record.weaknesses:
            raise ValidationException("AI Audit data is missing. Please run the AI Audit first.")

        score_record = await lead_score_repository.get_by_lead_id(db, lead_id=lead_id)
        if not score_record:
            raise ValidationException("Lead Score is missing. Please run the AI Audit and Scoring first.")

        generated_website = await generated_website_repository.get_latest_by_lead_id(db, lead_id=lead_id)
        preview_link = None
        if generated_website and generated_website.status in ("generated", "ready"):
            frontend_url = settings.FRONTEND_URL.rstrip("/")
            preview_link = f"{frontend_url}/preview/{generated_website.id}"

        lead_info = {
            "name": lead.name,
            "industry": lead.industry,
            "city": lead.city,
            "country": lead.country,
        }

        website_analysis = {
            "website_title": audit_record.website_title,
            "meta_description": audit_record.meta_description,
        }

        audit_data = {
            "weaknesses": audit_record.weaknesses,
            "verdict": audit_record.verdict,
            "executive_summary": audit_record.executive_summary
        }

        score_data = {
            "overall_score": score_record.overall_score,
            "category": score_record.category
        }

        # Fallback chain via shared run_chain
        async def _call(name: str):
            ai_provider = ai_factory.get_provider(name)
            return await ai_provider.generate_outreach(
                lead_info, website_analysis, audit_data, score_data
            )

        providers_to_try = ai_factory.get_fallback_chain(provider)
        chain_result = await run_chain(providers_to_try, _call)

        if not chain_result.success:
            raise ServiceUnavailableException(
                f"All providers failed for outreach. Last error: {chain_result.last_error}"
            )

        ai_result = chain_result.result

        cold_email = ai_result.get("Personalized Cold Email", "")
        followup_email = ai_result.get("Follow-up Email", "")
        if preview_link:
            preview_note = f"\n\n---\nView your AI-generated website preview: {preview_link}"
            if cold_email and preview_link not in cold_email:
                cold_email += preview_note
            if followup_email and preview_link not in followup_email:
                followup_email += preview_note

        outreach_data = {
            "email_subject": ai_result.get("Email Subject"),
            "cold_email": cold_email,
            "linkedin_message": ai_result.get("LinkedIn Message"),
            "followup_email": followup_email,
            "short_cta": ai_result.get("Short Call-To-Action"),
        }
        outreach_data["whatsapp_message"] = None

        existing = await outreach_repository.get_by_lead_id(db, lead_id=lead_id)
        if existing:
            updated_record = await outreach_repository.update(db, db_obj=existing, obj_in=outreach_data)
        else:
            create_schema = OutreachCreate(lead_id=lead_id, **outreach_data)
            updated_record = await outreach_repository.create(db, obj_in=create_schema)

        if lead.status == "ANALYZED":
            lead.status = "OUTREACH_READY"
            db.add(lead)
            await db.flush()

        logger.info("AI Outreach generated and saved | lead_id=%s", lead_id)
        return OutreachResponse.model_validate(updated_record)


outreach_service = OutreachService()
