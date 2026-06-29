from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.screenshot import CaptureScreenshotRequest, CaptureScreenshotResponse
from app.schemas.response import StandardResponse
from app.services.screenshot import screenshot_service

router = APIRouter()

@router.post(
    "/capture",
    response_model=StandardResponse[CaptureScreenshotResponse],
    status_code=status.HTTP_200_OK,
    summary="Capture and upload website screenshots",
    description=(
        "Captures desktop, mobile, and full-page screenshots of a lead's website "
        "using Playwright, waits for network idle, and uploads them to Cloudinary."
    ),
    responses={
        200: {"description": "Screenshots captured and uploaded successfully."},
        401: {"description": "Missing or invalid session credentials."},
        404: {"description": "Lead not found."},
        422: {"description": "Lead has no valid website URL."},
        503: {"description": "Playwright or Cloudinary service unavailable."},
    }
)
async def capture_screenshots(
    payload: CaptureScreenshotRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await screenshot_service.capture_screenshots(
        db,
        lead_id=payload.lead_id,
        user=current_user
    )
    
    return StandardResponse(
        success=True,
        message="Screenshots captured and uploaded successfully.",
        data=result
    )
