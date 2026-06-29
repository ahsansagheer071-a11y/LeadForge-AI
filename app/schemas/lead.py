import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

# Import sub-schemas for nested detailed responses
from app.schemas.lead_score import LeadScoreResponse
from app.schemas.audit import AuditResponse
from app.schemas.screenshot import ScreenshotResponse
from app.schemas.outreach import OutreachResponse


class LeadBase(BaseModel):
    name: str = Field(..., max_length=255)
    website: Optional[str] = Field(default=None, max_length=2083)
    phone: Optional[str] = Field(default=None, max_length=50)
    address: Optional[str] = Field(default=None, max_length=500)
    rating: Optional[float] = Field(default=None, ge=0.0, le=5.0)
    reviews_count: Optional[int] = Field(default=None, ge=0)
    maps_url: Optional[str] = Field(default=None, max_length=2083)
    city: str = Field(..., max_length=100)
    country: str = Field(..., max_length=100)
    industry: str = Field(..., max_length=100)
    status: str = Field(default="NEW", max_length=50)


class LeadCreate(LeadBase):
    user_id: uuid.UUID


class LeadUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    website: Optional[str] = Field(default=None, max_length=2083)
    phone: Optional[str] = Field(default=None, max_length=50)
    address: Optional[str] = Field(default=None, max_length=500)
    rating: Optional[float] = Field(default=None, ge=0.0, le=5.0)
    reviews_count: Optional[int] = Field(default=None, ge=0)
    maps_url: Optional[str] = Field(default=None, max_length=2083)
    city: Optional[str] = Field(default=None, max_length=100)
    country: Optional[str] = Field(default=None, max_length=100)
    industry: Optional[str] = Field(default=None, max_length=100)
    status: Optional[str] = Field(default=None, max_length=50)


class LeadResponse(LeadBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LeadDetailResponse(LeadResponse):
    """
    Complete consolidated information for a Lead, including score, audit, screenshot and outreach data.
    """
    score: Optional[LeadScoreResponse] = None
    audit: Optional[AuditResponse] = None
    screenshot: Optional[ScreenshotResponse] = None
    outreach: Optional[OutreachResponse] = None

    model_config = ConfigDict(from_attributes=True)


class LeadDiscoveryRequest(BaseModel):
    business_type: str = Field(..., min_length=1, max_length=100)
    city: str = Field(..., min_length=1, max_length=100)
    country: str = Field(..., min_length=1, max_length=100)


class LeadDiscoveryResponse(BaseModel):
    total_found: int = Field(..., ge=0)
    created: int = Field(..., ge=0)
    skipped_duplicates: int = Field(..., ge=0)
    leads: List[LeadResponse]

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Valid pipeline statuses — single source of truth
# ---------------------------------------------------------------------------
VALID_LEAD_STATUSES = frozenset([
    "NEW", "SCRAPED", "ANALYZED", "OUTREACH_READY", "CONTACTED", "CLOSED"
])


# ---------------------------------------------------------------------------
# Bulk action schemas
# ---------------------------------------------------------------------------

class BulkDeleteRequest(BaseModel):
    lead_ids: List[uuid.UUID] = Field(
        ..., min_length=1, max_length=500,
        description="List of lead UUIDs to delete (max 500 per request)"
    )


class BulkStatusUpdateRequest(BaseModel):
    lead_ids: List[uuid.UUID] = Field(
        ..., min_length=1, max_length=500,
        description="List of lead UUIDs to update"
    )
    status: str = Field(
        ..., description=f"New pipeline status. Allowed: {sorted(VALID_LEAD_STATUSES)}"
    )


class BulkActionResponse(BaseModel):
    processed: int = Field(..., description="Number of leads actually affected")
    not_found: int = Field(..., description="Number of lead_ids that were not found or not owned by user")
    lead_ids: List[uuid.UUID] = Field(..., description="IDs that were successfully processed")
