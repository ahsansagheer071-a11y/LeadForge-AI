import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class GeneratedWebsiteCreate(BaseModel):
    lead_id: uuid.UUID
    generation_id: str
    project_name: Optional[str] = None
    framework: str = "static-html"
    status: str = "generated"
    html: str
    preview_path: str
    package_id: Optional[str] = None
    package_metadata: Dict[str, Any] = Field(default_factory=dict)
    build_metadata: Dict[str, Any] = Field(default_factory=dict)


class GeneratedWebsiteUpdate(BaseModel):
    status: Optional[str] = None
    html: Optional[str] = None
    preview_path: Optional[str] = None
    package_id: Optional[str] = None
    package_metadata: Optional[Dict[str, Any]] = None
    build_metadata: Optional[Dict[str, Any]] = None


class GeneratedWebsiteResponse(BaseModel):
    id: uuid.UUID
    lead_id: uuid.UUID
    generation_id: str
    project_name: Optional[str] = None
    framework: str
    status: str
    html: str
    preview_path: str
    package_id: Optional[str] = None
    package_metadata: Dict[str, Any] = Field(default_factory=dict)
    build_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
