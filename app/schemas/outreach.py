import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class OutreachBase(BaseModel):
    email_subject: Optional[str] = None
    cold_email: Optional[str] = None
    followup_email: Optional[str] = None
    linkedin_message: Optional[str] = None
    whatsapp_message: Optional[str] = None
    short_cta: Optional[str] = None


class OutreachCreate(OutreachBase):
    lead_id: uuid.UUID


class OutreachUpdate(BaseModel):
    email_subject: Optional[str] = None
    cold_email: Optional[str] = None
    followup_email: Optional[str] = None
    linkedin_message: Optional[str] = None
    whatsapp_message: Optional[str] = None
    short_cta: Optional[str] = None


class OutreachResponse(OutreachBase):
    id: uuid.UUID
    lead_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GenerateOutreachRequest(BaseModel):
    lead_id: uuid.UUID = Field(..., description="The UUID of the lead to generate outreach for.")
    provider: str = Field(default="gemini", description="AI provider to use (e.g., 'gemini').")

