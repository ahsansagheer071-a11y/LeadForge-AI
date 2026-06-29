import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class LeadScoreBase(BaseModel):
    overall_score: int = Field(default=0, ge=0, le=100)
    seo_score: int = Field(default=0, ge=0, le=100)
    ux_score: int = Field(default=0, ge=0, le=100)
    branding_score: int = Field(default=0, ge=0, le=100)
    trust_score: int = Field(default=0, ge=0, le=100)
    conversion_score: int = Field(default=0, ge=0, le=100)
    category: str = Field(
        default="Cold Lead",
        description="Category: Hot Lead (90-100), Warm Lead (70-89), or Cold Lead (0-69)"
    )
    explanation: Optional[str] = None


class LeadScoreCreate(LeadScoreBase):
    lead_id: uuid.UUID


class LeadScoreUpdate(BaseModel):
    overall_score: Optional[int] = Field(default=None, ge=0, le=100)
    seo_score: Optional[int] = Field(default=None, ge=0, le=100)
    ux_score: Optional[int] = Field(default=None, ge=0, le=100)
    branding_score: Optional[int] = Field(default=None, ge=0, le=100)
    trust_score: Optional[int] = Field(default=None, ge=0, le=100)
    conversion_score: Optional[int] = Field(default=None, ge=0, le=100)
    category: Optional[str] = None
    explanation: Optional[str] = None


class LeadScoreResponse(LeadScoreBase):
    id: uuid.UUID
    lead_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
