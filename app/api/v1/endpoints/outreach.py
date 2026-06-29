from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.response import StandardResponse
from app.schemas.outreach import GenerateOutreachRequest, OutreachResponse
from app.services.outreach import outreach_service

router = APIRouter()

@router.post(
    "/generate",
    response_model=StandardResponse[OutreachResponse],
    status_code=status.HTTP_200_OK,
    summary="Generate personalized AI outreach",
    description=(
        "Generates highly personalized outreach templates (Cold Email, LinkedIn Message, "
        "Follow-up Email, Short CTA) by analyzing the lead's business context, website "
        "audit results, and lead score. Persists the generated outreach in the database."
    ),
    responses={
        200: {"description": "Outreach generated successfully."},
        401: {"description": "Missing or invalid session credentials."},
        404: {"description": "Lead not found."},
        422: {"description": "Prerequisite steps (Audit/Score) incomplete."},
        503: {"description": "AI service unavailable."}
    }
)
async def generate_outreach(
    payload: GenerateOutreachRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await outreach_service.generate_outreach(
        db,
        lead_id=payload.lead_id,
        user=current_user,
        provider=payload.provider
    )
    
    return StandardResponse(
        success=True,
        message="AI Outreach generated successfully.",
        data=result
    )
