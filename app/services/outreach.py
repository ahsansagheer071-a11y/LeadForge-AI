import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ValidationException
from app.core.logging import logger
from app.models.user import User
from app.repositories.lead import lead_repository
from app.repositories.audit import audit_repository
from app.repositories.lead_score import lead_score_repository
from app.repositories.outreach import outreach_repository
from app.schemas.outreach import OutreachCreate, OutreachResponse
from app.services.ai.factory import ai_factory

class OutreachService:
    """
    Orchestrates AI Outreach Generation. Loads required context (Lead, Analysis, Audit, Score),
    invokes the AI Provider, and persists the generated outreach templates.
    """

    async def generate_outreach(
        self,
        db: AsyncSession,
        *,
        lead_id: uuid.UUID,
        user: User,
        provider: str = "gemini"
    ) -> OutreachResponse:
        logger.info("Outreach generation initiated | lead_id=%s | provider=%s", lead_id, provider)

        # 1. Load lead
        lead = await lead_repository.get(db, id=lead_id)
        if not lead or lead.user_id != user.id:
            raise NotFoundException(f"Lead with id '{lead_id}' not found.")

        # 2. Load website analysis & audit details
        audit_record = await audit_repository.get_by_lead_id(db, lead_id=lead_id)
        if not audit_record:
            raise ValidationException("Please complete Website Analysis and AI Audit first.")
            
        if not audit_record.weaknesses:
            raise ValidationException("AI Audit data is missing. Please run the AI Audit first.")

        # 3. Load lead score
        score_record = await lead_score_repository.get_by_lead_id(db, lead_id=lead_id)
        if not score_record:
            raise ValidationException("Lead Score is missing. Please run the AI Audit and Scoring first.")

        # Prepare context payload for AI
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

        # 4. Invoke AI Provider
        ai_provider = ai_factory.get_provider(provider)
        ai_result = await ai_provider.generate_outreach(lead_info, website_analysis, audit_data, score_data)

        # 5. Persist Outreach Record
        outreach_data = {
            "email_subject": ai_result.get("Email Subject"),
            "cold_email": ai_result.get("Personalized Cold Email"),
            "linkedin_message": ai_result.get("LinkedIn Message"),
            "followup_email": ai_result.get("Follow-up Email"),
            "short_cta": ai_result.get("Short Call-To-Action"),
        }
        
        # We leave whatsapp_message None for now as it's not generated
        outreach_data["whatsapp_message"] = None

        existing = await outreach_repository.get_by_lead_id(db, lead_id=lead_id)
        if existing:
            updated_record = await outreach_repository.update(db, db_obj=existing, obj_in=outreach_data)
        else:
            create_schema = OutreachCreate(lead_id=lead_id, **outreach_data)
            updated_record = await outreach_repository.create(db, obj_in=create_schema)

        # Update lead status to OUTREACH_READY if applicable
        if lead.status == "ANALYZED":
            lead.status = "OUTREACH_READY"
            db.add(lead)
            await db.flush()

        logger.info("AI Outreach generated and saved | lead_id=%s", lead_id)
        return OutreachResponse.model_validate(updated_record)


outreach_service = OutreachService()
