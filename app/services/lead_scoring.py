import uuid
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ValidationException
from app.core.logging import logger
from app.models.user import User
from app.repositories.lead import lead_repository
from app.repositories.lead_score import lead_score_repository
from app.schemas.lead_score import LeadScoreCreate, LeadScoreResponse


class LeadScoringService:
    """
    Computes lead categorization (Hot, Warm, Cold) and detailed scores based on AI Audit findings.
    Persists data in the LeadScore table.
    """

    async def calculate_and_persist_score(
        self,
        db: AsyncSession,
        *,
        lead_id: uuid.UUID,
        user: User,
        ai_scores: Dict[str, Any]
    ) -> LeadScoreResponse:
        logger.info("Calculating lead score | lead_id=%s", lead_id)

        # Retrieve scores safely with fallbacks
        overall = int(ai_scores.get("Website Quality Score", 0))
        seo = int(ai_scores.get("SEO Score", 0))
        ux = int(ai_scores.get("Mobile Experience Score", 0))
        branding = int(ai_scores.get("Visual Design Score", 0))
        trust = int(ai_scores.get("Trust Score", 0))
        conversion = int(ai_scores.get("CTA Score", 0))

        # Categorize lead
        if overall >= 90:
            category = "Hot Lead"
        elif overall >= 70:
            category = "Warm Lead"
        else:
            category = "Cold Lead"

        # Generate explanation based on sub-scores
        lowest_score_name = "performance"
        lowest_val = 100
        sub_scores = {
            "SEO": seo,
            "Mobile Experience": ux,
            "Visual Design & Branding": branding,
            "Trust Indicators": trust,
            "Conversion Optimization": conversion
        }
        for name, val in sub_scores.items():
            if val < lowest_val:
                lowest_val = val
                lowest_score_name = name

        explanation = (
            f"This lead is categorized as a {category} with an overall website quality score of {overall}/100. "
            f"The primary bottleneck is {lowest_score_name} (scoring {lowest_val}/100). "
            f"Addressing this area offers the highest opportunity for client acquisition outreach."
        )

        score_data = {
            "overall_score": overall,
            "seo_score": seo,
            "ux_score": ux,
            "branding_score": branding,
            "trust_score": trust,
            "conversion_score": conversion,
            "category": category,
            "explanation": explanation
        }

        # Update or create database record
        existing = await lead_score_repository.get_by_lead_id(db, lead_id=lead_id)
        if existing:
            updated_record = await lead_score_repository.update(db, db_obj=existing, obj_in=score_data)
        else:
            create_schema = LeadScoreCreate(lead_id=lead_id, **score_data)
            updated_record = await lead_score_repository.create(db, obj_in=create_schema)

        # Update lead status to ANALYZED (ensure pipeline moves forward)
        lead = await lead_repository.get(db, id=lead_id)
        if lead and lead.status in ("NEW", "SCRAPED"):
            lead.status = "ANALYZED"
            db.add(lead)
            await db.flush()

        logger.info("Lead score successfully persisted | lead_id=%s | category=%s", lead_id, category)
        return LeadScoreResponse.model_validate(updated_record)


lead_scoring_service = LeadScoringService()
