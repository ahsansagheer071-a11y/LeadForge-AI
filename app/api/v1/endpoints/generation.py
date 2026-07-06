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
from app.core.exceptions import NotFoundException, ServiceUnavailableException
from app.repositories.lead import lead_repository

router = APIRouter()


class GenerateRequest(BaseModel):
    lead_id: uuid.UUID = Field(..., description="The UUID of the lead to generate a website for.")


class BuildProfileRequest(BaseModel):
    lead_id: uuid.UUID = Field(..., description="The UUID of the lead to build website intelligence for.")


class GenerateResponse(BaseModel):
    html: str
    generation_time: float = 0.0
    project_name: Optional[str] = None


@router.post(
    "/build",
    response_model=StandardResponse,
    status_code=status.HTTP_200_OK,
    summary="Build website intelligence profile for a lead",
    description=(
        "Uses Playwright to crawl the lead's website and extract structured data "
        "(brand identity, content sections, SEO metadata, design tokens, etc.). "
        "Required before generating a website."
    ),
    responses={
        200: {"description": "Profile built successfully."},
        404: {"description": "Lead not found or has no website URL."},
        503: {"description": "Playwright crawl failed."},
    }
)
async def build_website_intelligence(
    payload: BuildProfileRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lead = await lead_repository.get(db, id=payload.lead_id)
    if not lead:
        raise NotFoundException(f"Lead '{payload.lead_id}' not found.")
    if not lead.website:
        raise NotFoundException(f"Lead '{payload.lead_id}' has no website URL set.")

    profile = await website_intelligence_service.build_profile(
        db, lead=lead, url=lead.website
    )
    if not profile:
        raise ServiceUnavailableException(
            f"Failed to crawl website for lead '{payload.lead_id}'."
        )

    return StandardResponse(
        success=True,
        message="Website intelligence profile built successfully.",
        data={"lead_id": str(payload.lead_id)},
    )


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
    # 1. Fetch or build WebsiteProfile
    response = await website_intelligence_service.load_profile(
        db, lead_id=payload.lead_id
    )
    if not response:
        lead = await lead_repository.get(db, id=payload.lead_id)
        if not lead or not lead.website:
            raise NotFoundException(
                f"Website intelligence not found for lead {payload.lead_id}"
            )
        profile = await website_intelligence_service.build_profile(
            db, lead=lead, url=lead.website
        )
        if not profile:
            raise ServiceUnavailableException(
                f"Website crawl returned no profile for lead '{payload.lead_id}'."
            )
    else:
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
