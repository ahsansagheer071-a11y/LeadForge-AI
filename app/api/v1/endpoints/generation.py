import uuid
from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.response import StandardResponse
from app.services.website_intelligence import website_intelligence_service
from app.services.markdown_engine.builder import MarkdownBuilder
from app.services.website_generator.static_html_generator import StaticHTMLGenerator
from app.core.exceptions import NotFoundException

router = APIRouter()


class GenerateRequest(BaseModel):
    lead_id: uuid.UUID = Field(..., description="The UUID of the lead to generate a website for.")


class GenerateResponse(BaseModel):
    html: str
    generation_time: float = 0.0
    project_name: Optional[str] = None


@router.post(
    "/generate",
    response_model=StandardResponse[GenerateResponse],
    status_code=status.HTTP_200_OK,
    summary="Generate a static HTML website for a lead",
    description=(
        "Fetches the lead's WebsiteProfile and builds a MarkdownPackage, "
        "then runs the StaticHTMLGenerator to produce a single self-contained HTML file."
    ),
    responses={
        200: {"description": "Website generated successfully."},
        401: {"description": "Missing or invalid credentials."},
        404: {"description": "Lead or website intelligence data not found."},
        503: {"description": "AI Provider (Groq) is unavailable."},
    }
)
async def generate_website(
    payload: GenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1. Fetch WebsiteProfile
    response = await website_intelligence_service.load_profile(
        db, lead_id=payload.lead_id
    )
    if not response:
        raise NotFoundException(
            f"Website intelligence not found for lead {payload.lead_id}"
        )
    profile = response.profile

    # 2. Build MarkdownPackage from the profile
    builder = MarkdownBuilder(blueprint=profile)
    package = builder.build_package()

    # 3. Generate HTML
    generator = StaticHTMLGenerator()
    result = await generator.generate(blueprint=profile, package=package)

    if not result.success or not result.website_project:
        return StandardResponse(
            success=False,
            message="Generation failed: " + "; ".join(result.errors) if result.errors else "Unknown error",
            data=None,
        )

    html_content = result.website_project.files[0].content if result.website_project.files else ""

    return StandardResponse(
        success=True,
        message="Website generated successfully.",
        data=GenerateResponse(
            html=html_content,
            generation_time=result.generation_time,
            project_name=result.website_project.project_name,
        )
    )
