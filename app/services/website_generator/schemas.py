from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class GenerationContext(BaseModel):
    system_context: str = ""
    developer_context: str = ""
    branding_context: str = ""
    layout_context: str = ""
    components_context: str = ""
    animation_context: str = ""
    seo_context: str = ""
    performance_context: str = ""
    accessibility_context: str = ""
    assets_context: str = ""
    rules_context: str = ""
    output_context: str = ""
    generation_id: str = ""
    source_package_version: str = ""

    model_config = ConfigDict(frozen=True)


class PromptContext(BaseModel):
    system_context: str = ""
    developer_context: str = ""
    branding_context: str = ""
    layout_context: str = ""
    components_context: str = ""
    animation_context: str = ""
    seo_context: str = ""
    performance_context: str = ""
    accessibility_context: str = ""
    assets_context: str = ""
    rules_context: str = ""
    output_context: str = ""
    generation_constraints: str = ""

    model_config = ConfigDict(frozen=True)


class GeneratedFile(BaseModel):
    path: str
    content: str
    type: str
    size: int

    model_config = ConfigDict(from_attributes=True)


class GeneratedSection(BaseModel):
    section_name: str
    component_name: str
    source_markdown: str
    status: str

    model_config = ConfigDict(from_attributes=True)


class WebsiteProject(BaseModel):
    project_name: str
    framework: str
    generation_id: str
    version: str
    generated_at: datetime
    files: List[GeneratedFile] = Field(default_factory=list)
    assets: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    statistics: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class GenerationResult(BaseModel):
    success: bool = False
    website_project: Optional[WebsiteProject] = None
    generation_time: float = 0.0
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    provider_used: str = ""
    provider_attempts: int = 0

    model_config = ConfigDict(from_attributes=True)
