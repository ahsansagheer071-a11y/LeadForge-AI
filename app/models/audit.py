import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.lead import Lead


class Audit(Base):
    """
    SQLAlchemy model representing the deep website scraper details
    and multi-modal AI auditing findings for a lead.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    lead_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("leads.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False
    )
    
    # ----------------------------------------------------
    # Website Scraper Extract Data
    # ----------------------------------------------------
    website_title: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    meta_description: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True
    )
    emails: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        nullable=True
    )
    phone_numbers: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        nullable=True
    )
    contact_form_present: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    social_links: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        nullable=True
    )
    technologies: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        nullable=True
    )
    ssl_status: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    images: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        nullable=True
    )
    navigation_structure: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSON,
        nullable=True
    )
    cta_buttons: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSON,
        nullable=True
    )
    testimonials_present: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    faq_present: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    # ----------------------------------------------------
    # Website Analyzer – General
    # ----------------------------------------------------
    website_language: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True
    )
    https_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    http_status_code: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )

    # ----------------------------------------------------
    # Website Analyzer – Content Counts
    # ----------------------------------------------------
    h1_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    h2_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    total_paragraphs: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    total_images: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    total_forms: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    # ----------------------------------------------------
    # Website Analyzer – Navigation
    # ----------------------------------------------------
    contact_page_exists: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    about_page_exists: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    # ----------------------------------------------------
    # Website Analyzer – Social Presence
    # ----------------------------------------------------
    social_facebook: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    social_instagram: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    social_linkedin: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    social_twitter: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    social_youtube: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )

    # ----------------------------------------------------
    # Website Analyzer – SEO Flags
    # ----------------------------------------------------
    missing_meta_description: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    missing_h1: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    missing_title: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    # ----------------------------------------------------
    # Website Analyzer – Performance
    # ----------------------------------------------------
    html_size_kb: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )
    response_time_ms: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )

    # ----------------------------------------------------
    # AI Auditor Evaluation Findings
    # ----------------------------------------------------
    executive_summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    # List of weaknesses: [{"title": "...", "evidence": "...", "impact": "...", "recommendation": "..."}]
    weaknesses: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSON,
        nullable=True
    )
    
    verdict: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    lead: Mapped["Lead"] = relationship(
        "Lead",
        back_populates="audit"
    )
