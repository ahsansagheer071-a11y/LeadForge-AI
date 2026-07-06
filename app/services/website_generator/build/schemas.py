import uuid
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class BuildResult(BaseModel):
    success: bool = False
    project_path: Optional[str] = None
    build_path: Optional[str] = None
    npm_install_success: bool = False
    build_success: bool = False
    dev_server_started: bool = False
    server_url: Optional[str] = None
    server_pid: Optional[int] = None
    logs: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    install_duration: Optional[float] = None
    build_duration: Optional[float] = None
    total_duration: float = 0.0
    build_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])

    model_config = ConfigDict(from_attributes=True)


class ValidationReport(BaseModel):
    valid: bool = False
    missing_files: List[str] = Field(default_factory=list)
    invalid_files: List[str] = Field(default_factory=list)
    folder_errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    total_files_validated: int = 0

    model_config = ConfigDict(from_attributes=True)
