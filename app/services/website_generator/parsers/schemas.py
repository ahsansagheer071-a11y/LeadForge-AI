from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class GeneratedAsset(BaseModel):
    filename: str
    asset_type: str = "image"
    reference: str
    size_bytes: Optional[int] = None
    metadata: Dict[str, str] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class ProjectMetadata(BaseModel):
    provider: str = ""
    model: str = ""
    generation_time: float = 0.0
    framework_version: Optional[str] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class ProjectStatistics(BaseModel):
    total_files: int = 0
    total_assets: int = 0
    estimated_size_bytes: int = 0
    total_lines: Optional[int] = None
    components_count: Optional[int] = None
    pages_count: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
