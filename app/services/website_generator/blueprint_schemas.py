from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.services.website_intelligence.schemas import SectionInfo


class BlueprintPage(BaseModel):
    page_name: str
    route: str
    title: Optional[str] = None
    description: Optional[str] = None
    sections: List[SectionInfo] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class BlueprintAsset(BaseModel):
    filename: str
    asset_type: str = "image"
    reference: str
    metadata: Dict[str, str] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class WebsiteBlueprint(BaseModel):
    project_name: str = ""
    business_name: str = ""
    theme: Dict[str, str] = Field(default_factory=dict)
    pages: List[BlueprintPage] = Field(default_factory=list)
    navigation: Dict[str, Any] = Field(default_factory=dict)
    footer: Dict[str, Any] = Field(default_factory=dict)
    sections: List[SectionInfo] = Field(default_factory=list)
    assets: List[BlueprintAsset] = Field(default_factory=list)
    seo: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)
