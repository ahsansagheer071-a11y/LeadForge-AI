"""Schemas for the Stitch integration layer."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class StitchExportMeta(BaseModel):
    """Metadata about a Stitch export that was imported into LeadForge."""

    stitch_project_id: Optional[str] = None
    stitch_screen_id: Optional[str] = None
    exported_at: Optional[datetime] = None
    export_format: str = "html"
    source_brief_hash: Optional[str] = None
    stitch_model: Optional[str] = None
    generation_cost: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class StitchImportRequest(BaseModel):
    """Request schema for importing a Stitch HTML export."""

    lead_id: str
    html_content: str = Field(..., min_length=100, description="The full HTML content exported from Stitch")
    stitch_project_id: Optional[str] = None
    stitch_screen_id: Optional[str] = None
    export_format: str = "html"


class StitchBriefSection(BaseModel):
    """A single section of the redesign brief."""

    section_type: str
    title: str
    content_instructions: str
    source_content: List[str] = Field(default_factory=list)
    source_images: List[str] = Field(default_factory=list)
    design_notes: str = ""


class StitchDesignTokens(BaseModel):
    """Design tokens extracted from the WebsiteProfile for the brief."""

    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    background_color: Optional[str] = None
    text_color: Optional[str] = None
    heading_font: Optional[str] = None
    body_font: Optional[str] = None
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None


class PremiumRedesignBrief(BaseModel):
    """A complete Stitch redesign instruction generated from lead data.

    This brief is designed to be pasted into Google Stitch to generate
    a premium website redesign. It contains all the context Stitch needs
    to faithfully redesign the source website.
    """

    business_name: str
    business_url: str
    business_category: str = ""
    business_description: str = ""

    design_direction: str = "premium modern responsive"
    design_tokens: StitchDesignTokens = Field(default_factory=StitchDesignTokens)

    hero_section: StitchBriefSection = Field(default_factory=lambda: StitchBriefSection(
        section_type="hero", title="Hero Section", content_instructions=""
    ))
    sections: List[StitchBriefSection] = Field(default_factory=list)

    navigation_items: List[Dict[str, str]] = Field(default_factory=list)
    contact_info: Dict[str, str] = Field(default_factory=dict)
    social_links: List[Dict[str, str]] = Field(default_factory=list)

    original_images: List[Dict[str, str]] = Field(default_factory=list)
    logo_url: str = ""

    content_rules: List[str] = Field(default_factory=list)
    design_rules: List[str] = Field(default_factory=list)

    source_content_summary: str = ""
    full_instruction: str = ""

    model_config = ConfigDict(from_attributes=True)
