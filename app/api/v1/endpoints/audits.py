import uuid
from typing import Dict, Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.response import StandardResponse
from app.services.audit_engine import audit_engine_service
from app.services.lead_scoring import lead_scoring_service
from app.schemas.lead_score import LeadScoreResponse

router = APIRouter()


class AuditRequest(BaseModel):
    lead_id: uuid.UUID = Field(..., description="The UUID of the lead to analyze.")
    provider: str = Field(default="groq", description="AI provider to use (e.g., 'groq').")


class AuditAndScoreResult(BaseModel):
    lead_id: uuid.UUID
    audit: Dict[str, Any] = Field(..., description="Raw output dictionary from the AI Audit Engine.")
    score: LeadScoreResponse = Field(..., description="The calculated and persisted lead score details.")


@router.post(
    "/run",
    response_model=StandardResponse[AuditAndScoreResult],
    status_code=status.HTTP_200_OK,
    summary="Run AI Audit and Lead Scoring",
    description=(
        "Triggers the AI Audit Engine to scan the lead context, website analysis, "
        "and screenshots. Calculates the final overall score and category (Hot/Warm/Cold), "
        "and stores/updates records in both the Audit and LeadScore tables."
    ),
    responses={
        200: {"description": "AI Audit and Lead Scoring completed successfully."},
        401: {"description": "Missing or invalid credentials."},
        404: {"description": "Lead or website analysis record not found."},
        422: {"description": "Missing prerequisite steps (website analysis)."},
        503: {"description": "AI Provider (Groq) is unavailable."},
    }
)
async def run_audit_and_scoring(
    payload: AuditRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1. Run AI Audit
    ai_audit_data = await audit_engine_service.generate_audit(
        db,
        lead_id=payload.lead_id,
        user=current_user,
        provider=payload.provider
    )

    # 2. Run Lead Scoring
    score_response = await lead_scoring_service.calculate_and_persist_score(
        db,
        lead_id=payload.lead_id,
        user=current_user,
        ai_scores=ai_audit_data
    )

    result = AuditAndScoreResult(
        lead_id=payload.lead_id,
        audit=ai_audit_data,
        score=score_response
    )

    return StandardResponse(
        success=True,
        message="AI Audit and Lead Scoring completed successfully.",
        data=result
    )
