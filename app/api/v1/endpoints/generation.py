import uuid
from io import BytesIO
from typing import Optional
from zipfile import ZIP_DEFLATED, ZipFile
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.generated_website import GeneratedWebsite
from app.schemas.generated_website import GeneratedWebsiteCreate, GeneratedWebsiteResponse
from app.schemas.response import StandardResponse
from app.services.website_intelligence import website_intelligence_service
from app.services.markdown_engine.builder import MarkdownBuilder
from app.services.website_generator.static_html_generator import StaticHTMLGenerator
from app.services.website_generator.build.schemas import BuildResult
from app.services.website_generator.deployment.package_manager import PackageManager
from app.services.website_generator.preview.schemas import PreviewResult
from app.core.exceptions import NotFoundException, ServiceUnavailableException
from app.repositories.lead import lead_repository
from app.repositories.generated_website import generated_website_repository

router = APIRouter()


class GenerateRequest(BaseModel):
    lead_id: uuid.UUID = Field(..., description="The UUID of the lead to generate a website for.")


class BuildProfileRequest(BaseModel):
    lead_id: uuid.UUID = Field(..., description="The UUID of the lead to build website intelligence for.")


class GenerateResponse(BaseModel):
    website_id: uuid.UUID
    lead_id: uuid.UUID
    generation_id: str
    html: str
    generation_time: float = 0.0
    project_name: Optional[str] = None
    preview_path: str
    package_id: Optional[str] = None
    status: str = "generated"


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
    lead = await lead_repository.get(db, id=payload.lead_id)
    if not lead or lead.user_id != current_user.id:
        raise NotFoundException(f"Lead '{payload.lead_id}' not found.")

    # 1. Fetch or build WebsiteProfile
    response = await website_intelligence_service.load_profile(
        db, lead_id=payload.lead_id
    )
    if not response:
        if not lead.website:
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
    preview_record = GeneratedWebsite(
        lead_id=payload.lead_id,
        generation_id=result.website_project.generation_id,
        project_name=result.website_project.project_name,
        framework=result.website_project.framework,
        status="generated",
        html=html_content,
        preview_path="",
        build_metadata={
            "generation_time": result.generation_time,
            "warnings": result.warnings,
            "file_count": len(result.website_project.files),
        },
    )
    db.add(preview_record)
    await db.flush()

    preview_record.preview_path = f"/preview/{preview_record.id}"

    build_result = BuildResult(
        success=True,
        build_success=True,
        npm_install_success=True,
        logs=["Static HTML generated; no Next.js build required for iframe preview."],
    )
    preview_result = PreviewResult(
        success=True,
        preview_url=preview_record.preview_path,
        status="ready",
        health_check=True,
    )
    package = PackageManager().create_package(
        result.website_project,
        build_result,
        preview_result,
    )
    preview_record.package_id = package.package_id
    preview_record.package_metadata = package.model_dump(mode="json")
    db.add(preview_record)
    await db.commit()
    await db.refresh(preview_record)

    return StandardResponse(
        success=True,
        message="Website generated successfully.",
        data=GenerateResponse(
            website_id=preview_record.id,
            lead_id=payload.lead_id,
            generation_id=result.website_project.generation_id,
            html=html_content,
            generation_time=result.generation_time,
            project_name=result.website_project.project_name,
            preview_path=preview_record.preview_path,
            package_id=preview_record.package_id,
            status=preview_record.status,
        )
    )


async def _get_owned_generated_website(
    db: AsyncSession,
    website_id: uuid.UUID,
    current_user: User,
) -> GeneratedWebsite:
    website = await generated_website_repository.get(db, id=website_id)
    if not website:
        raise NotFoundException(f"Generated website '{website_id}' not found.")

    lead = await lead_repository.get(db, id=website.lead_id)
    if not lead or lead.user_id != current_user.id:
        raise NotFoundException(f"Generated website '{website_id}' not found.")
    return website


@router.get(
    "/websites/{website_id}",
    response_model=StandardResponse[GeneratedWebsiteResponse],
    status_code=status.HTTP_200_OK,
    summary="Load a persisted generated website preview",
)
async def get_generated_website(
    website_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    website = await _get_owned_generated_website(db, website_id, current_user)
    return StandardResponse(
        success=True,
        message="Generated website retrieved successfully.",
        data=GeneratedWebsiteResponse.model_validate(website),
    )


@router.get(
    "/leads/{lead_id}/latest",
    response_model=StandardResponse[GeneratedWebsiteResponse],
    status_code=status.HTTP_200_OK,
    summary="Load the latest generated website for a lead",
)
async def get_latest_generated_website(
    lead_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lead = await lead_repository.get(db, id=lead_id)
    if not lead or lead.user_id != current_user.id:
        raise NotFoundException(f"Lead '{lead_id}' not found.")
    website = await generated_website_repository.get_latest_by_lead_id(db, lead_id=lead_id)
    if not website:
        raise NotFoundException("No generated website exists for this lead yet.")
    return StandardResponse(
        success=True,
        message="Latest generated website retrieved successfully.",
        data=GeneratedWebsiteResponse.model_validate(website),
    )


@router.get(
    "/websites/{website_id}/download",
    status_code=status.HTTP_200_OK,
    summary="Download the generated website deployment package",
)
async def download_generated_website_package(
    website_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    website = await _get_owned_generated_website(db, website_id, current_user)
    if website.status not in {"generated", "ready"}:
        raise ServiceUnavailableException("This generated website is not ready for download.")

    package = website.package_metadata or {}
    artifacts = package.get("artifacts") if isinstance(package, dict) else None
    if not artifacts:
        raise NotFoundException("No deployment package is available for this generated website.")

    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as zf:
        for artifact in artifacts:
            if not isinstance(artifact, dict):
                continue
            content = artifact.get("content")
            path = artifact.get("path") or artifact.get("name")
            if content is None or not path:
                continue
            zf.writestr(str(path).lstrip("/\\"), str(content))
        zf.writestr("leadforge-package.json", __import__("json").dumps(package, indent=2))

    buffer.seek(0)
    safe_name = (website.project_name or "leadforge-website").lower()
    safe_name = "".join(ch if ch.isalnum() else "-" for ch in safe_name).strip("-") or "leadforge-website"
    filename = f"{safe_name}-{website.id}.zip"
    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
