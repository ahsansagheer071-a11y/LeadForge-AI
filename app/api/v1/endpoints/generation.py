"""Async Generation Jobs endpoint.

Production Railway deployments have a ~30-second proxy timeout on synchronous
requests.  Website generation (crawl + AI call) routinely takes 60-180 seconds
for complex business sites, so a synchronous /generate call will always be
killed by the proxy before it completes.

This module implements an async job pattern using the database:
  POST /api/v1/generation/jobs        → { job_id, status: "pending" }
  GET  /api/v1/generation/jobs/{id}   → { status, result, error, progress }

The background task runs the full pipeline and writes the result into the
persistent `generation_jobs` table. The frontend polls GET every 3 seconds.
"""

import base64
import logging
import uuid
from datetime import datetime, timezone
from enum import Enum
from io import BytesIO
from typing import Any, Optional
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi import APIRouter, BackgroundTasks, Depends, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ServiceUnavailableException
from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.generated_website import GeneratedWebsite
from app.models.generation_job import GenerationJob as DBGenerationJob
from app.models.user import User
from app.repositories.generated_website import generated_website_repository
from app.repositories.lead import lead_repository
from app.schemas.generated_website import GeneratedWebsiteResponse
from app.schemas.response import StandardResponse
from app.services.markdown_engine.builder import MarkdownBuilder
from app.services.website_generator.deployment.package_manager import PackageManager
from app.services.website_generator.design_provider import DesignProviderNotConfigured
from app.services.website_generator.stitch.import_provider import StitchImportProvider
from app.services.website_generator.stitch.brief import BriefGenerator
from app.services.website_intelligence import website_intelligence_service
from app.services.website_intelligence.schemas import WebsiteProfile

logger = logging.getLogger(__name__)

router = APIRouter()


class JobStatus(str, Enum):
    PENDING   = "pending"
    RUNNING   = "running"
    SUCCEEDED = "succeeded"
    FAILED    = "failed"


# ---------------------------------------------------------------------------
# Background worker
# ---------------------------------------------------------------------------

async def _update_job_status(db: AsyncSession, job_id: str, status: JobStatus, progress: str, error: Optional[str] = None, **kwargs):
    stmt = select(DBGenerationJob).filter_by(job_id=job_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()
    if job:
        job.status = status.value
        job.progress = progress
        if error:
            job.error = error
        for k, v in kwargs.items():
            setattr(job, k, v)
        db.add(job)
        await db.commit()
    return job

async def _run_generation_job(job_id: str, lead_id: uuid.UUID, user_id: str) -> None:
    """Background task: full generation pipeline, writes result into database."""
    # We need a fresh DB session since we are running outside the request lifecycle
    from app.database.session import AsyncSessionLocal

    try:
        async with AsyncSessionLocal() as db:
            await _update_job_status(db, job_id, JobStatus.RUNNING, "Loading lead data")

            lead = await lead_repository.get(db, id=lead_id)
            if not lead or str(lead.user_id) != user_id:
                await _update_job_status(db, job_id, JobStatus.FAILED, "Failed", error=f"Lead '{lead_id}' not found or access denied.")
                return

            # ── Step 1: Profile ──────────────────────────────────────────── #
            await _update_job_status(db, job_id, JobStatus.RUNNING, "Loading lead data")
            response = await website_intelligence_service.load_profile(db, lead_id=lead_id)
            needs_rebuild = (
                response
                and not (response.profile.products or [])
                and not (response.profile.services or [])
            )
            if needs_rebuild:
                logger.info("[GEN] Cached profile has 0 products and 0 services — re-crawling for %s", lead_id)
                response = None
            if not response:
                if not lead.website:
                    await _update_job_status(db, job_id, JobStatus.FAILED, "Failed", error="No website URL on this lead and no cached profile.")
                    return
                await _update_job_status(db, job_id, JobStatus.RUNNING, "Crawling website (fresh)")
                profile = await website_intelligence_service.build_profile(
                    db, lead=lead, url=lead.website
                )
                if not profile:
                    await _update_job_status(db, job_id, JobStatus.FAILED, "Failed", error="Website crawl returned no usable data. The site may block bots.")
                    return
            else:
                profile = response.profile

            # ── Step 2: Markdown package ─────────────────────────────────── #
            await _update_job_status(db, job_id, JobStatus.RUNNING, "Building markdown context")
            builder  = MarkdownBuilder(blueprint=profile)
            package  = builder.build_package()

            # ── Step 3: Design generation ────────────────────────────────── #
            await _update_job_status(db, job_id, JobStatus.RUNNING, "Generating design")
            provider = StitchImportProvider()
            result   = await provider.generate(profile, package)

            if not result.success or not result.website_project:
                error_msg = "; ".join(result.errors) if result.errors else "Design provider unavailable"
                await _update_job_status(
                    db, job_id, JobStatus.FAILED, "Failed",
                    error=error_msg,
                    provider_used=provider.provider_name(),
                )
                return

            # ── Step 4: Persist ──────────────────────────────────────────── #
            await _update_job_status(db, job_id, JobStatus.RUNNING, "Saving result")
            preview_html = getattr(result.website_project, 'preview_html', None)
            html_content  = result.website_project.files[0].content if result.website_project.files else ""
            preview_record = GeneratedWebsite(
                lead_id      = lead_id,
                generation_id= result.website_project.generation_id,
                project_name = result.website_project.project_name,
                framework    = result.website_project.framework,
                status       = "generated",
                html         = preview_html or html_content,
                preview_path = "",
                build_metadata={
                    "generation_time":   result.generation_time,
                    "warnings":          result.warnings,
                    "file_count":        len(result.website_project.files),
                    "provider_used":     result.provider_used,
                    "provider_attempts": result.provider_attempts,
                },
            )
            db.add(preview_record)
            await db.flush()

            preview_record.preview_path = f"/preview/{preview_record.id}"

            from app.services.website_generator.build.schemas import BuildResult
            from app.services.website_generator.preview.schemas import PreviewResult
            build_result = BuildResult(
                success=True, build_success=True, npm_install_success=True,
                logs=["Design generated."],
            )
            preview_result = PreviewResult(
                success=True, preview_url=preview_record.preview_path,
                status="ready", health_check=True,
            )
            pkg = PackageManager().create_package(result.website_project, build_result, preview_result)
            preview_record.package_id       = pkg.package_id
            preview_record.package_metadata = pkg.model_dump(mode="json")
            db.add(preview_record)
            await db.commit()
            await db.refresh(preview_record)

            # ── Write success into job ────────────────────────────────────── #
            await _update_job_status(
                db, job_id, JobStatus.SUCCEEDED, "Complete",
                website_id      = str(preview_record.id),
                generation_id   = result.website_project.generation_id,
                html            = preview_html or html_content,
                preview_path    = preview_record.preview_path,
                package_id      = preview_record.package_id,
                project_name    = result.website_project.project_name,
                provider_used   = result.provider_used,
                generation_time = result.generation_time
            )

    except Exception as exc:
        logger.exception("Generation job %s failed: %s", job_id, exc)
        async with AsyncSessionLocal() as db:
            await _update_job_status(db, job_id, JobStatus.FAILED, "Failed", error=f"{type(exc).__name__}: {exc}")


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class CreateJobRequest(BaseModel):
    lead_id: uuid.UUID = Field(..., description="UUID of the lead to generate a website for.")


class JobStatusResponse(BaseModel):
    job_id:          str
    lead_id:         str
    status:          str
    progress:        str
    website_id:      Optional[str] = None
    generation_id:   Optional[str] = None
    html:            Optional[str] = None
    preview_path:    Optional[str] = None
    package_id:      Optional[str] = None
    project_name:    Optional[str] = None
    provider_used:   Optional[str] = None
    generation_time: float = 0.0
    error:           Optional[str] = None


class GenerateRequest(BaseModel):
    lead_id: uuid.UUID = Field(..., description="The UUID of the lead to generate a website for.")


class BuildProfileRequest(BaseModel):
    lead_id: uuid.UUID = Field(..., description="The UUID of the lead to build website intelligence for.")


class GenerateResponse(BaseModel):
    website_id:     uuid.UUID
    lead_id:        uuid.UUID
    generation_id:  str
    html:           str
    generation_time: float = 0.0
    project_name:   Optional[str] = None
    preview_path:   str
    package_id:     Optional[str] = None
    status:         str = "generated"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

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
    "/jobs",
    response_model=StandardResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit an async website generation job",
    description=(
        "Immediately returns a job_id.  The generation runs in the background "
        "(crawl + AI call).  Poll GET /jobs/{job_id} until status is "
        "'succeeded' or 'failed'."
    ),
)
async def create_generation_job(
    payload: CreateJobRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Quick ownership check before queuing
    lead = await lead_repository.get(db, id=payload.lead_id)
    if not lead or lead.user_id != current_user.id:
        raise NotFoundException(f"Lead '{payload.lead_id}' not found.")

    # Check for existing active jobs for this lead
    stmt = select(DBGenerationJob).filter(
        DBGenerationJob.lead_id == payload.lead_id,
        DBGenerationJob.status.in_(["pending", "running"])
    )
    result = await db.execute(stmt)
    existing_job = result.scalar_one_or_none()
    
    if existing_job:
        return StandardResponse(
            success=True,
            message="Active generation job already exists for this lead.",
            data={"job_id": existing_job.job_id, "status": existing_job.status},
        )

    job_id = uuid.uuid4().hex
    
    db_job = DBGenerationJob(
        job_id=job_id,
        lead_id=payload.lead_id,
        user_id=current_user.id,
        status=JobStatus.PENDING.value,
        progress="Queued",
    )
    db.add(db_job)
    await db.commit()

    background_tasks.add_task(
        _run_generation_job,
        job_id  = job_id,
        lead_id = payload.lead_id,
        user_id = str(current_user.id),
    )

    logger.info(
        "Generation job queued | job_id=%s | lead_id=%s | user=%s",
        job_id, payload.lead_id, current_user.id,
    )

    return StandardResponse(
        success=True,
        message="Generation job queued.",
        data={"job_id": job_id, "status": "pending"},
    )


@router.get(
    "/jobs/{job_id}",
    response_model=StandardResponse[JobStatusResponse],
    status_code=status.HTTP_200_OK,
    summary="Poll a generation job for status and result",
)
async def get_generation_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(DBGenerationJob).filter_by(job_id=job_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()
    
    if not job:
        raise NotFoundException(f"Job '{job_id}' not found.")
    if str(job.user_id) != str(current_user.id):
        raise NotFoundException(f"Job '{job_id}' not found.")

    return StandardResponse(
        success=True,
        message=f"Job status: {job.status}",
        data=JobStatusResponse(
            job_id          = job.job_id,
            lead_id         = str(job.lead_id),
            status          = job.status,
            progress        = job.progress,
            website_id      = job.website_id,
            generation_id   = job.generation_id,
            html            = job.html,
            preview_path    = job.preview_path,
            package_id      = job.package_id,
            project_name    = job.project_name,
            provider_used   = job.provider_used,
            generation_time = job.generation_time,
            error           = job.error,
        ),
    )


@router.post(
    "/generate",
    response_model=StandardResponse[GenerateResponse],
    status_code=status.HTTP_200_OK,
    summary="Generate a static HTML website for a lead (synchronous)",
    description=(
        "Fetches the lead's WebsiteProfile and builds a MarkdownPackage, "
        "then delegates to the configured DesignProvider. "
        "Note: prefer POST /jobs for production use to avoid proxy timeouts."
    ),
    responses={
        200: {"description": "Website generated successfully."},
        401: {"description": "Missing or invalid credentials."},
        404: {"description": "Lead or website intelligence data not found."},
        503: {"description": "AI Provider is unavailable."},
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
    needs_rebuild = (
        response
        and not (response.profile.products or [])
        and not (response.profile.services or [])
    )
    if needs_rebuild:
        response = None
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

    # 3. Generate design
    provider = StitchImportProvider()
    result = await provider.generate(profile, package)

    if not result.success or not result.website_project:
        return StandardResponse(
            success=False,
            message="; ".join(result.errors) if result.errors else "Design provider unavailable",
            data=None,
        )

    preview_html = getattr(result.website_project, 'preview_html', None)
    html_content = result.website_project.files[0].content if result.website_project.files else ""
    preview_record = GeneratedWebsite(
        lead_id=payload.lead_id,
        generation_id=result.website_project.generation_id,
        project_name=result.website_project.project_name,
        framework=result.website_project.framework,
        status="generated",
        html=preview_html or html_content,
        preview_path="",
        build_metadata={
            "generation_time": result.generation_time,
            "warnings": result.warnings,
            "file_count": len(result.website_project.files),
            "provider_used": result.provider_used,
            "provider_attempts": result.provider_attempts,
        },
    )
    db.add(preview_record)
    await db.flush()

    preview_record.preview_path = f"/preview/{preview_record.id}"

    from app.services.website_generator.build.schemas import BuildResult
    from app.services.website_generator.preview.schemas import PreviewResult
    build_result = BuildResult(
        success=True,
        build_success=True,
        npm_install_success=True,
        logs=["Design generated."],
    )
    preview_result = PreviewResult(
        success=True,
        preview_url=preview_record.preview_path,
        status="ready",
        health_check=True,
    )
    package_obj = PackageManager().create_package(
        result.website_project,
        build_result,
        preview_result,
    )
    preview_record.package_id = package_obj.package_id
    preview_record.package_metadata = package_obj.model_dump(mode="json")
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
            encoding = artifact.get("encoding")
            clean_path = str(path).lstrip("/\\")
            if encoding == "base64":
                try:
                    decoded = base64.b64decode(content)
                    zf.writestr(clean_path, decoded)
                except Exception:
                    zf.writestr(clean_path, str(content))
            else:
                zf.writestr(clean_path, str(content))

    buffer.seek(0)
    safe_name = (website.project_name or "leadforge-website").lower()
    safe_name = "".join(ch if ch.isalnum() else "-" for ch in safe_name).strip("-") or "leadforge-website"
    filename = f"{safe_name}-{website.id}.zip"
    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# Stitch import endpoints
# ---------------------------------------------------------------------------

class StitchImportRequest(BaseModel):
    lead_id: uuid.UUID = Field(..., description="UUID of the lead.")
    html_content: str = Field(..., min_length=100, description="Full HTML exported from Google Stitch.")
    stitch_project_id: Optional[str] = Field(None, description="Stitch project ID if available.")
    stitch_screen_id: Optional[str] = Field(None, description="Stitch screen ID if available.")


class StitchBriefRequest(BaseModel):
    lead_id: uuid.UUID = Field(..., description="UUID of the lead to generate a brief for.")
    weaknesses: Optional[list[str]] = Field(None, description="Audit weaknesses to address.")
    recommendations: Optional[list[str]] = Field(None, description="Audit recommendations to implement.")


@router.post(
    "/stitch/import",
    response_model=StandardResponse,
    status_code=status.HTTP_200_OK,
    summary="Import a Stitch HTML export into LeadForge",
    description=(
        "Accepts HTML exported from Google Stitch, validates it, "
        "and persists it as a GeneratedWebsite with preview and ZIP package."
    ),
)
async def import_stitch_export(
    payload: StitchImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lead = await lead_repository.get(db, id=payload.lead_id)
    if not lead or lead.user_id != current_user.id:
        raise NotFoundException(f"Lead '{payload.lead_id}' not found.")

    validation_issues = StitchImportProvider.validate_export(payload.html_content)
    critical = [i for i in validation_issues if "empty" in i.lower() or "too short" in i.lower()]
    if critical:
        return StandardResponse(
            success=False,
            message="Stitch export validation failed.",
            data={"issues": critical},
        )

    response = await website_intelligence_service.load_profile(db, lead_id=payload.lead_id)
    profile = response.profile if response else WebsiteProfile(
        business={"name": lead.company or "", "website_url": lead.website or ""},
    )

    builder = MarkdownBuilder(blueprint=profile)
    package = builder.build_package()

    provider = StitchImportProvider()
    result = await provider.generate(
        profile, package,
        html_content=payload.html_content,
        stitch_project_id=payload.stitch_project_id,
        stitch_screen_id=payload.stitch_screen_id,
    )

    if not result.success or not result.website_project:
        error_msg = "; ".join(result.errors) if result.errors else "Import failed"
        return StandardResponse(success=False, message=error_msg, data=None)

    preview_html = result.website_project.preview_html or ""
    html_content = result.website_project.files[0].content if result.website_project.files else ""

    preview_record = GeneratedWebsite(
        lead_id=payload.lead_id,
        generation_id=result.website_project.generation_id,
        project_name=result.website_project.project_name,
        framework=result.website_project.framework,
        status="generated",
        html=preview_html or html_content,
        preview_path="",
        build_metadata={
            "generation_time": result.generation_time,
            "warnings": result.warnings,
            "file_count": len(result.website_project.files),
            "provider_used": result.provider_used,
            "stitch_project_id": payload.stitch_project_id,
            "stitch_screen_id": payload.stitch_screen_id,
        },
    )
    db.add(preview_record)
    await db.flush()

    preview_record.preview_path = f"/preview/{preview_record.id}"

    from app.services.website_generator.build.schemas import BuildResult
    from app.services.website_generator.preview.schemas import PreviewResult
    build_result = BuildResult(
        success=True, build_success=True, npm_install_success=True,
        logs=["Stitch export imported."],
    )
    preview_result = PreviewResult(
        success=True, preview_url=preview_record.preview_path,
        status="ready", health_check=True,
    )
    pkg = PackageManager().create_package(result.website_project, build_result, preview_result)
    preview_record.package_id = pkg.package_id
    preview_record.package_metadata = pkg.model_dump(mode="json")
    db.add(preview_record)
    await db.commit()
    await db.refresh(preview_record)

    warnings = []
    if validation_issues:
        warnings = validation_issues

    return StandardResponse(
        success=True,
        message="Stitch export imported successfully.",
        data={
            "website_id": str(preview_record.id),
            "lead_id": str(payload.lead_id),
            "generation_id": result.website_project.generation_id,
            "preview_path": preview_record.preview_path,
            "package_id": preview_record.package_id,
            "provider_used": result.provider_used,
            "warnings": warnings,
        },
    )


@router.post(
    "/stitch/brief",
    response_model=StandardResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate a PremiumRedesignBrief for Google Stitch",
    description=(
        "Builds a complete redesign instruction from the lead's WebsiteProfile. "
        "Copy this brief into Google Stitch to generate a premium redesign."
    ),
)
async def generate_stitch_brief(
    payload: StitchBriefRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lead = await lead_repository.get(db, id=payload.lead_id)
    if not lead or lead.user_id != current_user.id:
        raise NotFoundException(f"Lead '{payload.lead_id}' not found.")

    response = await website_intelligence_service.load_profile(db, lead_id=payload.lead_id)
    if not response:
        if not lead.website:
            raise NotFoundException(f"No website intelligence for lead '{payload.lead_id}'.")
        profile = await website_intelligence_service.build_profile(db, lead=lead, url=lead.website)
        if not profile:
            raise ServiceUnavailableException("Website crawl failed.")
    else:
        profile = response.profile

    builder = MarkdownBuilder(blueprint=profile)
    package = builder.build_package()

    gen = BriefGenerator()
    brief = gen.generate(
        profile, package,
        weaknesses=payload.weaknesses,
        recommendations=payload.recommendations,
    )

    return StandardResponse(
        success=True,
        message="PremiumRedesignBrief generated.",
        data={
            "business_name": brief.business_name,
            "brief_hash": gen.brief_hash(brief),
            "full_instruction": brief.full_instruction,
            "sections_count": len(brief.sections),
            "images_count": len(brief.original_images),
            "rules_count": len(brief.content_rules) + len(brief.design_rules),
        },
    )


@router.post(
    "/stitch/validate",
    response_model=StandardResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate a Stitch HTML export without importing",
)
async def validate_stitch_export(
    html_content: str,
    current_user: User = Depends(get_current_user),
):
    issues = StitchImportProvider.validate_export(html_content)
    return StandardResponse(
        success=len(issues) == 0,
        message="Export is valid." if not issues else f"{len(issues)} issue(s) found.",
        data={"issues": issues, "valid": len(issues) == 0},
    )
