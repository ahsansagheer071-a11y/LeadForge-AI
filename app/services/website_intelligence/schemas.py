from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class RgbColor(BaseModel):
    r: int
    g: int
    b: int


class HslColor(BaseModel):
    h: float
    s: float
    l: float


class ComputedColor(BaseModel):
    hex: str
    rgb: RgbColor
    hsl: HslColor
    relative_brightness: float
    frequency: int = 0
    usage_role: Optional[str] = None


class ContrastPair(BaseModel):
    foreground: str
    background: str
    contrast_ratio: float
    wcag_compliance: str
    element_pair: str


class ColorPalette(BaseModel):
    primary: Optional[str] = None
    secondary: Optional[str] = None
    accent: Optional[str] = None
    background: Optional[str] = None
    text: Optional[str] = None
    surface: Optional[str] = None
    heading: Optional[str] = None
    border: Optional[str] = None
    muted: Optional[str] = None
    dark: Optional[str] = None
    light: Optional[str] = None
    success: Optional[str] = None
    warning: Optional[str] = None
    danger: Optional[str] = None
    info: Optional[str] = None
    computed_colors: Dict[str, ComputedColor] = Field(default_factory=dict)
    contrast_ratios: Dict[str, float] = Field(default_factory=dict)
    wcag_compliance: Dict[str, str] = Field(default_factory=dict)
    poor_combinations: List[ContrastPair] = Field(default_factory=list)
    accessibility_score: Optional[float] = None


class FontInfo(BaseModel):
    family: str
    weight: Optional[str] = None
    usage: Optional[str] = None


class Typography(BaseModel):
    fonts: List[FontInfo] = Field(default_factory=list)
    heading_h1: Optional[str] = None
    heading_h2: Optional[str] = None
    heading_h3: Optional[str] = None
    body: Optional[str] = None
    heading_font: Optional[str] = None
    body_font: Optional[str] = None


class NavigationItem(BaseModel):
    label: str
    url: str
    children: List["NavigationItem"] = Field(default_factory=list)


class NavItem(BaseModel):
    label: str
    url: str
    order: int = 0
    has_dropdown: bool = False
    is_mega_menu: bool = False
    dropdown_items: List["NavItem"] = Field(default_factory=list)


class NavigationInfo(BaseModel):
    primary_nav_items: List[NavItem] = Field(default_factory=list)
    secondary_nav_items: List[NavItem] = Field(default_factory=list)
    footer_nav_items: List[NavItem] = Field(default_factory=list)
    navigation_depth: int = 0
    is_sticky: bool = False


class HeroSection(BaseModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    cta_buttons: List[Dict[str, Any]] = Field(default_factory=list)
    background_image: Optional[str] = None


class CtaButton(BaseModel):
    text: str
    url: str
    position: str = "hero"


class HeroInfo(BaseModel):
    hero_title: Optional[str] = None
    hero_subtitle: Optional[str] = None
    hero_description: Optional[str] = None
    primary_cta: Optional[CtaButton] = None
    secondary_cta: Optional[CtaButton] = None
    ctas: List[CtaButton] = Field(default_factory=list)
    hero_image: Optional[str] = None
    background_image_url: Optional[str] = None
    background_color: Optional[str] = None
    hero_layout: Optional[str] = None
    hero_alignment: Optional[str] = None
    hero_height: Optional[int] = None
    is_fallback_detection: bool = False
    # Aliases for downstream compatibility
    title: Optional[str] = None
    subtitle: Optional[str] = None
    description: Optional[str] = None
    layout: Optional[str] = None


class ServiceCard(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    image: Optional[str] = None
    features: List[str] = Field(default_factory=list)
    title: Optional[str] = None
    subtitle: Optional[str] = None
    short_description: Optional[str] = None
    full_description: Optional[str] = None
    category: Optional[str] = None
    order_on_page: int = 0
    section_selector: Optional[str] = None
    source_url: Optional[str] = None
    cta: Optional[CtaLink] = None
    price: Optional[str] = None
    currency: Optional[str] = None
    badge: Optional[str] = None


class ProductItem(BaseModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    short_description: Optional[str] = None
    full_description: Optional[str] = None
    icon: Optional[str] = None
    image: Optional[str] = None
    category: Optional[str] = None
    order_on_page: int = 0
    section_selector: Optional[str] = None
    source_url: Optional[str] = None
    cta: Optional[CtaLink] = None
    price: Optional[str] = None
    currency: Optional[str] = None
    badge: Optional[str] = None


class ContactInfo(BaseModel):
    emails: List[str] = Field(default_factory=list)
    phones: List[str] = Field(default_factory=list)
    address: Optional[str] = None
    contact_form_present: bool = False
    contact_form_fields: List[str] = Field(default_factory=list)
    map_coordinates: Optional[Dict[str, float]] = None


class CtaLink(BaseModel):
    text: str
    url: str


class SectionInfo(BaseModel):
    section_type: str = "Other"
    order: int = 0
    heading: Optional[str] = None
    subheading: Optional[str] = None
    description: Optional[str] = None
    layout_type: str = "single-column"
    images: List[str] = Field(default_factory=list)
    buttons: List[CtaLink] = Field(default_factory=list)
    confidence_score: float = 0.0


class CTAInfo(BaseModel):
    text: str
    url: Optional[str] = None
    button_type: str = "link"
    is_primary: bool = False
    is_placeholder_link: bool = False
    position: int = 0
    section: Optional[str] = None


class FooterInfo(BaseModel):
    footer_logo: Optional[str] = None
    footer_description: Optional[str] = None
    footer_links: List[NavItem] = Field(default_factory=list)
    contact_info: ContactInfo = Field(default_factory=ContactInfo)
    social_links: List[SocialLink] = Field(default_factory=list)
    copyright_text: Optional[str] = None
    newsletter_signup: bool = False
    newsletter_action_url: Optional[str] = None
    is_fallback_detection: bool = False


class WebsiteLayout(BaseModel):
    sections: List[SectionInfo] = Field(default_factory=list)
    ctas: List[CTAInfo] = Field(default_factory=list)
    footer_info: Optional[FooterInfo] = None


class ImageAsset(BaseModel):
    url: str
    alt: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    type: Optional[str] = None


class SocialLink(BaseModel):
    platform: str
    url: str
    icon: Optional[str] = None


class Testimonial(BaseModel):
    author: Optional[str] = None
    role: Optional[str] = None
    company: Optional[str] = None
    content: str
    avatar: Optional[str] = None
    rating: Optional[int] = None
    author_name: Optional[str] = None
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    avatar_url: Optional[str] = None
    review_text: Optional[str] = None
    review_date: Optional[str] = None
    platform: Optional[str] = None
    source_url: Optional[str] = None
    section_position: int = 0
    order: int = 0
    verified_badge: bool = False
    star_count: Optional[int] = None
    associated_service: Optional[str] = None


class FAQ(BaseModel):
    question: str
    answer: str
    category: Optional[str] = None
    order: int = 0
    section_title: Optional[str] = None
    section_selector: Optional[str] = None
    collapsed_by_default: bool = True
    expanded_by_default: bool = False


class TeamMember(BaseModel):
    name: str
    role: Optional[str] = None
    bio: Optional[str] = None
    image: Optional[str] = None
    social_links: List[SocialLink] = Field(default_factory=list)
    full_name: Optional[str] = None
    job_title: Optional[str] = None
    department: Optional[str] = None
    photo_url: Optional[str] = None
    email: Optional[str] = None
    linkedin: Optional[str] = None
    twitter: Optional[str] = None
    facebook: Optional[str] = None
    instagram: Optional[str] = None
    years_experience: Optional[str] = None
    qualifications: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    display_order: int = 0


class CompanySection(BaseModel):
    section_title: Optional[str] = None
    section_type: Optional[str] = None
    description: Optional[str] = None
    mission: Optional[str] = None
    vision: Optional[str] = None
    core_values: List[str] = Field(default_factory=list)
    years_in_business: Optional[str] = None
    company_size: Optional[str] = None
    business_type: Optional[str] = None
    target_audience: Optional[str] = None
    industries_served: List[str] = Field(default_factory=list)
    usp: Optional[str] = None


class TrustSignal(BaseModel):
    type: str
    value: str
    source_url: Optional[str] = None
    description: Optional[str] = None


class BusinessInfo(BaseModel):
    name: str = ""
    legal_name: Optional[str] = None
    category: str = ""
    industry: Optional[str] = None
    description: Optional[str] = None
    logo: Optional[str] = None
    favicon: Optional[str] = None
    website_url: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    google_maps_url: Optional[str] = None
    opening_hours: Optional[str] = None
    founded_year: Optional[int] = None
    employee_count: Optional[str] = None
    social_links: List[SocialLink] = Field(default_factory=list)


class LogoInfo(BaseModel):
    logo_url: Optional[str] = None
    format: Optional[str] = None
    has_transparent_background: Optional[bool] = None
    estimated_width: Optional[int] = None
    estimated_height: Optional[int] = None
    dominant_colors: List[str] = Field(default_factory=list)
    position: Optional[str] = None
    is_retina_quality: bool = False
    is_favicon_fallback: bool = False


class FontFallback(BaseModel):
    family: str
    is_system_font: bool = False


class HierarchyEntry(BaseModel):
    font_size: Optional[str] = None
    line_height: Optional[str] = None
    letter_spacing: Optional[str] = None
    font_weight: Optional[int] = None
    font_family: Optional[str] = None


class TypographyInfo(BaseModel):
    primary_font: Optional[str] = None
    heading_font: Optional[str] = None
    secondary_font: Optional[str] = None
    fallback_stack: List[FontFallback] = Field(default_factory=list)
    is_google_font: bool = False
    is_system_font: bool = False
    weights_used: List[int] = Field(default_factory=list)
    hierarchy: Dict[str, HierarchyEntry] = Field(default_factory=dict)


class DesignLanguageEntry(BaseModel):
    name: str
    score: float = 0.0
    matched_signals: Dict[str, List[str]] = Field(default_factory=dict)


class DesignLanguageResult(BaseModel):
    design_language: str = "Unclassified"
    confidence_score: float = 0.0
    all_scores: Dict[str, float] = Field(default_factory=dict)


class BrandPersonalityTrait(BaseModel):
    trait: str
    score: float = 0.0
    matched_signals: Dict[str, List[str]] = Field(default_factory=dict)


class BrandPersonalityResult(BaseModel):
    personality_traits: List[str] = Field(default_factory=list)
    confidence_percentages: Dict[str, float] = Field(default_factory=dict)


class ConsistencyReport(BaseModel):
    color_consistency: Optional[float] = None
    spacing_consistency: Optional[float] = None
    typography_consistency: Optional[float] = None
    button_consistency: Optional[float] = None
    card_consistency: Optional[float] = None
    border_radius_consistency: Optional[float] = None
    shadow_consistency: Optional[float] = None
    overall_consistency_score: Optional[float] = None
    component_counts: Dict[str, int] = Field(default_factory=dict)
    skipped_components: List[str] = Field(default_factory=list)


class ComponentStyles(BaseModel):
    component_styles: Dict[str, Dict[str, str]] = Field(default_factory=dict)


class BrandIdentity(BaseModel):
    tagline: Optional[str] = None
    brand_voice: Optional[str] = None
    target_audience: Optional[str] = None
    unique_selling_points: List[str] = Field(default_factory=list)
    brand_colors: ColorPalette = Field(default_factory=ColorPalette)
    brand_typography: Typography = Field(default_factory=Typography)
    logo_info: Optional[LogoInfo] = None
    typography_info: Optional[TypographyInfo] = None
    design_language: Optional[DesignLanguageResult] = None
    brand_personality: Optional[BrandPersonalityResult] = None
    consistency_report: Optional[ConsistencyReport] = None
    component_styles: Optional[ComponentStyles] = None


class SEOInfo(BaseModel):
    page_title: Optional[str] = None
    meta_description: Optional[str] = None
    focus_keywords: List[str] = Field(default_factory=list)
    missing_meta_description: bool = False
    missing_title: bool = False
    missing_h1: bool = False
    https_enabled: bool = False
    ssl_status: bool = False


class CallToAction(BaseModel):
    text: str
    url: Optional[str] = None
    type: Optional[str] = None
    color: Optional[str] = None


class QualityMetric(BaseModel):
    score: int
    grade: str
    status: str
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class QualityMetrics(BaseModel):
    content_quality: QualityMetric = Field(default_factory=lambda: QualityMetric(score=0, grade="F", status="Not Analyzed"))
    navigation_quality: QualityMetric = Field(default_factory=lambda: QualityMetric(score=0, grade="F", status="Not Analyzed"))
    visual_consistency: QualityMetric = Field(default_factory=lambda: QualityMetric(score=0, grade="F", status="Not Analyzed"))
    contact_completeness: QualityMetric = Field(default_factory=lambda: QualityMetric(score=0, grade="F", status="Not Analyzed"))
    trust_level: QualityMetric = Field(default_factory=lambda: QualityMetric(score=0, grade="F", status="Not Analyzed"))
    social_presence: QualityMetric = Field(default_factory=lambda: QualityMetric(score=0, grade="F", status="Not Analyzed"))
    seo_readiness: QualityMetric = Field(default_factory=lambda: QualityMetric(score=0, grade="F", status="Not Analyzed"))
    accessibility_readiness: QualityMetric = Field(default_factory=lambda: QualityMetric(score=0, grade="F", status="Not Analyzed"))
    conversion_readiness: QualityMetric = Field(default_factory=lambda: QualityMetric(score=0, grade="F", status="Not Analyzed"))
    mobile_readiness: QualityMetric = Field(default_factory=lambda: QualityMetric(score=0, grade="F", status="Not Analyzed"))
    professionalism_score: QualityMetric = Field(default_factory=lambda: QualityMetric(score=0, grade="F", status="Not Analyzed"))


class WebsiteBlueprint(BaseModel):
    navbar_info: Dict[str, Any] = Field(default_factory=dict)
    hero: Dict[str, Any] = Field(default_factory=dict)
    services: Dict[str, Any] = Field(default_factory=dict)
    about: Dict[str, Any] = Field(default_factory=dict)
    why_choose_us: Dict[str, Any] = Field(default_factory=dict)
    portfolio: Dict[str, Any] = Field(default_factory=dict)
    testimonials: Dict[str, Any] = Field(default_factory=dict)
    faq: Dict[str, Any] = Field(default_factory=dict)
    pricing: Dict[str, Any] = Field(default_factory=dict)
    contact: Dict[str, Any] = Field(default_factory=dict)
    footer: Dict[str, Any] = Field(default_factory=dict)
    color_palette: Dict[str, Any] = Field(default_factory=dict)
    typography: Dict[str, Any] = Field(default_factory=dict)
    spacing: Dict[str, Any] = Field(default_factory=dict)
    sections_order: List[str] = Field(default_factory=list)
    missing_sections: List[str] = Field(default_factory=list)
    recommended_sections: List[Dict[str, str]] = Field(default_factory=list)
    image_requirements: List[Dict[str, Any]] = Field(default_factory=list)
    brand_style: Dict[str, Any] = Field(default_factory=dict)
    animations_needed: List[Dict[str, Any]] = Field(default_factory=list)
    components_required: List[Dict[str, Any]] = Field(default_factory=list)


class WebsiteProfile(BaseModel):
    business: BusinessInfo = Field(default_factory=BusinessInfo)
    brand: BrandIdentity = Field(default_factory=BrandIdentity)
    seo: SEOInfo = Field(default_factory=SEOInfo)
    colors: ColorPalette = Field(default_factory=ColorPalette)
    typography: Typography = Field(default_factory=Typography)
    navigation: List[NavigationItem] = Field(default_factory=list)
    navigation_info: Optional[NavigationInfo] = None
    hero: HeroSection = Field(default_factory=HeroSection)
    hero_info: Optional[HeroInfo] = None
    website_layout: Optional[WebsiteLayout] = None
    services: List[ServiceCard] = Field(default_factory=list)
    products: List[ProductItem] = Field(default_factory=list)
    contact: ContactInfo = Field(default_factory=ContactInfo)
    images: List[ImageAsset] = Field(default_factory=list)
    testimonials: List[Testimonial] = Field(default_factory=list)
    faqs: List[FAQ] = Field(default_factory=list)
    team: List[TeamMember] = Field(default_factory=list)
    company: Optional[CompanySection] = None
    trust_signals: List[TrustSignal] = Field(default_factory=list)
    blog_links: List[Dict[str, Any]] = Field(default_factory=list)
    social_links: List[SocialLink] = Field(default_factory=list)
    call_to_actions: List[CallToAction] = Field(default_factory=list)
    statistics: Dict[str, Any] = Field(default_factory=dict)
    website_summary: Optional[str] = None
    raw_html_size_kb: Optional[float] = None
    quality_metrics: Optional[QualityMetrics] = None
    blueprint: Optional[WebsiteBlueprint] = None
    extraction_timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)


class WebsiteIntelligenceResponse(BaseModel):
    lead_id: uuid.UUID
    website_url: str
    profile: WebsiteProfile

    model_config = ConfigDict(from_attributes=True)


class WebsiteIntelligenceRequest(BaseModel):
    lead_id: uuid.UUID = Field(..., description="The UUID of the lead to extract intelligence from.")