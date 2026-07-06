import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class WeaknessItem(BaseModel):
    title: str = Field(..., description="Short title of the identified weakness")
    evidence: str = Field(..., description="Technical or design evidence observed on the website")
    impact: str = Field(..., description="Impact of this issue on business or conversions")
    recommendation: str = Field(..., description="Actionable recommendation to solve this issue")


class AuditBase(BaseModel):
    # Website Scraper Data
    website_title: Optional[str] = None
    meta_description: Optional[str] = None
    emails: Optional[List[str]] = Field(default_factory=list)
    phone_numbers: Optional[List[str]] = Field(default_factory=list)
    contact_form_present: bool = False
    social_links: Optional[List[str]] = Field(default_factory=list)
    technologies: Optional[List[str]] = Field(default_factory=list)
    ssl_status: bool = False
    images: Optional[List[str]] = Field(default_factory=list)
    navigation_structure: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    cta_buttons: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    testimonials_present: bool = False
    faq_present: bool = False

    # Website Analyzer – General
    website_language: Optional[str] = None
    https_enabled: bool = False
    http_status_code: Optional[int] = None

    # Website Analyzer – Content Counts
    h1_count: int = 0
    h2_count: int = 0
    total_paragraphs: int = 0
    total_images: int = 0
    total_forms: int = 0

    # Website Analyzer – Navigation
    contact_page_exists: bool = False
    about_page_exists: bool = False

    # Website Analyzer – Social Presence
    social_facebook: Optional[str] = None
    social_instagram: Optional[str] = None
    social_linkedin: Optional[str] = None
    social_twitter: Optional[str] = None
    social_youtube: Optional[str] = None

    # Website Analyzer – SEO Flags
    missing_meta_description: bool = False
    missing_h1: bool = False
    missing_title: bool = False

    # Website Analyzer – Performance
    html_size_kb: Optional[float] = None
    response_time_ms: Optional[float] = None

    # AI Evaluation Findings
    executive_summary: Optional[str] = None
    weaknesses: Optional[List[str]] = Field(default_factory=list)
    verdict: Optional[str] = None


class AuditCreate(AuditBase):
    lead_id: uuid.UUID


class AuditUpdate(BaseModel):
    website_title: Optional[str] = None
    meta_description: Optional[str] = None
    emails: Optional[List[str]] = None
    phone_numbers: Optional[List[str]] = None
    contact_form_present: Optional[bool] = None
    social_links: Optional[List[str]] = None
    technologies: Optional[List[str]] = None
    ssl_status: Optional[bool] = None
    images: Optional[List[str]] = None
    navigation_structure: Optional[List[Dict[str, Any]]] = None
    cta_buttons: Optional[List[Dict[str, Any]]] = None
    testimonials_present: Optional[bool] = None
    faq_present: Optional[bool] = None

    # Website Analyzer fields
    website_language: Optional[str] = None
    https_enabled: Optional[bool] = None
    http_status_code: Optional[int] = None
    h1_count: Optional[int] = None
    h2_count: Optional[int] = None
    total_paragraphs: Optional[int] = None
    total_images: Optional[int] = None
    total_forms: Optional[int] = None
    contact_page_exists: Optional[bool] = None
    about_page_exists: Optional[bool] = None
    social_facebook: Optional[str] = None
    social_instagram: Optional[str] = None
    social_linkedin: Optional[str] = None
    social_twitter: Optional[str] = None
    social_youtube: Optional[str] = None
    missing_meta_description: Optional[bool] = None
    missing_h1: Optional[bool] = None
    missing_title: Optional[bool] = None
    html_size_kb: Optional[float] = None
    response_time_ms: Optional[float] = None

    # AI fields
    executive_summary: Optional[str] = None
    weaknesses: Optional[List[str]] = None
    verdict: Optional[str] = None


class AuditResponse(AuditBase):
    id: uuid.UUID
    lead_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------
# Website Analyzer Endpoint Schemas
# -------------------------------------------------------

class WebsiteAnalysisRequest(BaseModel):
    """Request body for POST /api/v1/analysis/website."""
    lead_id: uuid.UUID = Field(..., description="The UUID of the lead whose website will be analyzed.")


class WebsiteAnalysisResponse(BaseModel):
    """Structured result returned after analysing a lead's website."""

    lead_id: uuid.UUID
    website_url: str

    # General
    page_title: Optional[str] = None
    meta_description: Optional[str] = None
    website_language: Optional[str] = None
    https_enabled: bool = False
    http_status_code: Optional[int] = None

    # Content
    h1_count: int = 0
    h2_count: int = 0
    total_paragraphs: int = 0
    total_images: int = 0
    total_forms: int = 0

    # Business Information
    emails: List[str] = Field(default_factory=list)
    phone_numbers: List[str] = Field(default_factory=list)

    # Navigation
    contact_page_exists: bool = False
    about_page_exists: bool = False

    # Social Presence
    social_facebook: Optional[str] = None
    social_instagram: Optional[str] = None
    social_linkedin: Optional[str] = None
    social_twitter: Optional[str] = None
    social_youtube: Optional[str] = None

    # SEO
    missing_meta_description: bool = False
    missing_h1: bool = False
    missing_title: bool = False

    # Performance
    html_size_kb: Optional[float] = None
    response_time_ms: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)
