from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.audit import WebsiteAnalysisRequest, WebsiteAnalysisResponse
from app.schemas.response import StandardResponse
from app.services.website_analyzer import website_analyzer_service

router = APIRouter()


@router.post(
    "/website",
    response_model=StandardResponse[WebsiteAnalysisResponse],
    status_code=status.HTTP_200_OK,
    summary="Analyze a lead's website",
    description=(
        "Downloads the homepage of the lead's website, parses the HTML, "
        "and extracts structured intelligence including page metadata, "
        "content structure, business contact info, social links, SEO flags, "
        "and performance metrics. Results are stored in the Audit table."
    ),
    responses={
        200: {"description": "Website analyzed successfully."},
        401: {"description": "Missing or invalid session credentials."},
        404: {"description": "Lead not found."},
        422: {"description": "Lead has no website URL or URL is invalid."},
        503: {"description": "Website is unreachable or timed out."},
    },
)
async def analyze_website(
    payload: WebsiteAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await website_analyzer_service.analyze(
        db,
        lead_id=payload.lead_id,
        user=current_user,
    )

    return StandardResponse(
        success=True,
        message="Website analyzed successfully.",
        data=result,
    )
