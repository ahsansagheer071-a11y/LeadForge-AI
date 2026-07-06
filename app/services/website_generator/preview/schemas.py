from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class PreviewResult(BaseModel):
    success: bool = False
    preview_url: Optional[str] = None
    local_url: str = "http://localhost:3000"
    server_pid: Optional[int] = None
    host: str = "localhost"
    port: int = 3000
    status: str = "starting"
    startup_time: float = 0.0
    health_check: bool = False
    response_time_ms: Optional[float] = None
    logs: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    last_checked: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class InstanceInfo(BaseModel):
    pid: int
    port: int
    url: str
    project_path: str
    started_at: datetime
    status: str = "running"
    last_health_check: Optional[datetime] = None
    health_check_count: int = 0

    model_config = ConfigDict(from_attributes=True)
