import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class WebsiteIntelligence(Base):
    """
    SQLAlchemy model representing the comprehensive extracted website intelligence
    for a lead. Each lead has exactly one intelligence record storing structured
    data about business info, brand identity, design system, content sections,
    SEO, and more.
    """

    __tablename__ = "website_intelligence"

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

    # --------------------------------------------------------
    # Business Information
    # --------------------------------------------------------
    business_name: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    business_legal_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    business_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    business_industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    business_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    favicon_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    website_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    google_maps_url: Mapped[Optional[str]] = mapped_column(String(2083), nullable=True)
    opening_hours: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    founded_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    employee_count: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    social_links: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)

    # --------------------------------------------------------
    # Website Summary
    # --------------------------------------------------------
    website_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # --------------------------------------------------------
    # Brand Voice
    # --------------------------------------------------------
    brand_tagline: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    brand_voice: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    brand_unique_selling_points: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)

    # --------------------------------------------------------
    # Logo Info
    # --------------------------------------------------------
    logo_info_url: Mapped[Optional[str]] = mapped_column(String(2083), nullable=True)
    logo_info_format: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    logo_info_has_transparency: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    logo_info_width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    logo_info_height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    logo_info_dominant_colors: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    logo_info_position: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    logo_info_retina_quality: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    logo_info_is_favicon_fallback: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # --------------------------------------------------------
    # Target Audience
    # --------------------------------------------------------
    target_audience: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # --------------------------------------------------------
    # Color Palette
    # --------------------------------------------------------
    color_primary: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    color_secondary: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    color_accent: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    color_background: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    color_text: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    color_surface: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    color_heading: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    color_border: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    color_muted: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    color_dark: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    color_light: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    color_success: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    color_warning: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    color_danger: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    color_info: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    color_computed_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    color_contrast_ratios: Mapped[Optional[Dict[str, float]]] = mapped_column(JSON, nullable=True)
    color_wcag_compliance: Mapped[Optional[Dict[str, str]]] = mapped_column(JSON, nullable=True)
    color_poor_combinations: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)
    color_accessibility_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # --------------------------------------------------------
    # Typography
    # --------------------------------------------------------
    fonts: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)
    heading_h1: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    heading_h2: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    heading_h3: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    body_font: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    typography_primary_font: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    typography_heading_font: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    typography_secondary_font: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    typography_fallback_stack: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)
    typography_is_google_font: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    typography_is_system_font: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    typography_weights_used: Mapped[Optional[List[int]]] = mapped_column(JSON, nullable=True)
    typography_hierarchy: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # --------------------------------------------------------
    # Design Language
    # --------------------------------------------------------
    design_language_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    design_language_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    design_language_all_scores: Mapped[Optional[Dict[str, float]]] = mapped_column(JSON, nullable=True)

    # --------------------------------------------------------
    # Brand Personality
    # --------------------------------------------------------
    brand_personality_traits: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    brand_personality_scores: Mapped[Optional[Dict[str, float]]] = mapped_column(JSON, nullable=True)

    # --------------------------------------------------------
    # Visual Consistency
    # --------------------------------------------------------
    consistency_overall_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    consistency_color_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    consistency_spacing_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    consistency_typography_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    consistency_button_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    consistency_card_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    consistency_border_radius_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    consistency_shadow_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    consistency_component_counts: Mapped[Optional[Dict[str, int]]] = mapped_column(JSON, nullable=True)
    consistency_skipped_components: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)

    # --------------------------------------------------------
    # Component Styles
    # --------------------------------------------------------
    component_styles: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # --------------------------------------------------------
    # Navigation
    # --------------------------------------------------------
    navigation_items: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)
    navigation_logo: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_sticky_nav: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    nav_primary_items: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)
    nav_secondary_items: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)
    nav_footer_items: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)
    nav_depth: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # --------------------------------------------------------
    # Hero Section
    # --------------------------------------------------------
    hero_title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    hero_subtitle: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    hero_cta_buttons: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)
    hero_background_image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    hero_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hero_image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    hero_primary_cta: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    hero_secondary_cta: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    hero_background_image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    hero_background_color: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    hero_layout: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    hero_alignment: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    hero_height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_fallback_detection: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sections: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)
    ctas: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)
    footer_logo: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    footer_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    footer_links: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)
    footer_contact_emails: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    footer_contact_phones: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    footer_contact_address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    footer_social_links: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)
    footer_copyright: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    footer_newsletter_signup: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    footer_newsletter_action: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    footer_is_fallback: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # --------------------------------------------------------
    # Services & Products
    # --------------------------------------------------------
    services: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)
    products: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)

    # --------------------------------------------------------
    # Contact Information
    # --------------------------------------------------------
    contact_emails: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    contact_phones: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    contact_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    contact_form_present: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    contact_form_fields: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    contact_map_coordinates: Mapped[Optional[Dict[str, float]]] = mapped_column(JSON, nullable=True)

    # --------------------------------------------------------
    # Images
    # --------------------------------------------------------
    images: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)

    # --------------------------------------------------------
    # Testimonials
    # --------------------------------------------------------
    testimonials: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)

    # --------------------------------------------------------
    # FAQs
    # --------------------------------------------------------
    faqs: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)

    # --------------------------------------------------------
    # Team
    # --------------------------------------------------------
    team_members: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)
    company_info: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    trust_signals: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------
    statistics: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # --------------------------------------------------------
    # Blog
    # --------------------------------------------------------
    blog_links: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)

    # --------------------------------------------------------
    # Social Links
    # --------------------------------------------------------
    social_links_present: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)

    # --------------------------------------------------------
    # SEO
    # --------------------------------------------------------
    seo_page_title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    seo_meta_description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    seo_focus_keywords: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    seo_missing_meta_description: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    seo_missing_title: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    seo_missing_h1: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    seo_https_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    seo_ssl_status: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # --------------------------------------------------------
    # Call To Actions
    # --------------------------------------------------------
    call_to_actions: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)

    # --------------------------------------------------------
    # Quality Metrics
    # --------------------------------------------------------
    quality_metrics: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    website_blueprint: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # --------------------------------------------------------
    # Metadata
    # --------------------------------------------------------
    raw_html_size_kb: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    extraction_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
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