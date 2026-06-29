import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ScreenshotBase(BaseModel):
    desktop_local_path: Optional[str] = None
    desktop_cloudinary_url: Optional[str] = None
    desktop_public_id: Optional[str] = None

    mobile_local_path: Optional[str] = None
    mobile_cloudinary_url: Optional[str] = None
    mobile_public_id: Optional[str] = None

    full_page_local_path: Optional[str] = None
    full_page_cloudinary_url: Optional[str] = None
    full_page_public_id: Optional[str] = None


class ScreenshotCreate(ScreenshotBase):
    lead_id: uuid.UUID


class ScreenshotUpdate(ScreenshotBase):
    pass


class ScreenshotResponse(ScreenshotBase):
    id: uuid.UUID
    lead_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CaptureScreenshotRequest(BaseModel):
    lead_id: uuid.UUID = Field(..., description="The UUID of the lead to capture screenshots for.")


class CaptureScreenshotResponse(BaseModel):
    lead_id: uuid.UUID
    desktop_url: Optional[str] = None
    mobile_url: Optional[str] = None
    full_page_url: Optional[str] = None

