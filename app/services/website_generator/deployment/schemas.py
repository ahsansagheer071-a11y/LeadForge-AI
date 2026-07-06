import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class DeploymentArtifact(BaseModel):
    name: str
    path: str
    type: str = "file"
    size: int = 0
    checksum: Optional[str] = None
    content: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class DeploymentManifest(BaseModel):
    framework: str = ""
    version: str = ""
    generated_at: datetime = Field(default_factory=datetime.now)
    provider: str = ""
    model: str = ""
    build_status: str = "unknown"
    preview_status: str = "unknown"
    total_files: int = 0
    total_assets: int = 0
    total_size: int = 0
    generation_id: str = ""
    build_id: str = ""
    checksum: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DeploymentPackage(BaseModel):
    package_id: str = Field(
        default_factory=lambda: uuid.uuid4().hex[:12]
    )
    project_name: str = ""
    framework: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    project_path: Optional[str] = None
    preview_url: Optional[str] = None
    build_result: Dict[str, Any] = Field(default_factory=dict)
    manifest: Dict[str, Any] = Field(default_factory=dict)
    artifacts: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
