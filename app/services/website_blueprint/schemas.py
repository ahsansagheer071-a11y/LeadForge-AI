import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class BlueprintNavigation(BaseModel):
    style: str = "default"
    sticky: bool = True
    primary_links: List[Dict[str, str]] = Field(default_factory=list)
    secondary_links: List[Dict[str, str]] = Field(default_factory=list)
    cta_button: Optional[Dict[str, str]] = None
    mobile_breakpoint: str = "768px"
    menu_style: str = "dropdown"

    model_config = ConfigDict(from_attributes=True)


class BlueprintFooter(BaseModel):
    columns: int = 4
    show_logo: bool = True
    show_description: bool = True
    show_contact: bool = True
    show_social: bool = True
    show_newsletter: bool = False
    show_copyright: bool = True
    layout: str = "multi-column"

    model_config = ConfigDict(from_attributes=True)


class BlueprintSection(BaseModel):
    section_type: str
    display_name: str = ""
    order: int = 0
    required: bool = True
    layout: str = "default"
    columns: int = 1
    heading: Optional[str] = None
    subheading: Optional[str] = None
    description: Optional[str] = None
    image_count: int = 0
    component_count: int = 0
    animation_style: Optional[str] = None
    background_style: str = "light"
    priority: int = 5
    confidence: int = 100

    model_config = ConfigDict(from_attributes=True)


class BlueprintLayout(BaseModel):
    container_width: str = "1200px"
    container_type: str = "boxed"
    section_spacing: str = "80px"
    grid_gap: str = "24px"
    content_alignment: str = "center"
    border_radius: str = "8px"
    shadow_style: str = "soft"
    responsive_breakpoints: Dict[str, str] = Field(default_factory=lambda: {
        "mobile": "480px",
        "tablet": "768px",
        "desktop": "1024px",
        "wide": "1280px",
    })

    model_config = ConfigDict(from_attributes=True)


class BlueprintColorPalette(BaseModel):
    primary: Optional[str] = None
    secondary: Optional[str] = None
    accent: Optional[str] = None
    background: Optional[str] = None
    surface: Optional[str] = None
    text: Optional[str] = None
    muted: Optional[str] = None
    success: str = "#10B981"
    warning: str = "#F59E0B"
    danger: str = "#EF4444"
    info: str = "#3B82F6"

    model_config = ConfigDict(from_attributes=True)


class BlueprintTypography(BaseModel):
    heading_font: Optional[str] = None
    body_font: Optional[str] = None
    secondary_font: Optional[str] = None
    heading_weights: List[int] = Field(default_factory=lambda: [600, 700])
    body_weight: int = 400
    base_size: str = "16px"
    scale_ratio: str = "1.25"
    heading_scale: Dict[str, str] = Field(default_factory=lambda: {
        "h1": "2.5rem", "h2": "2.0rem", "h3": "1.75rem",
        "h4": "1.5rem", "h5": "1.25rem", "h6": "1.0rem",
    })
    body_scale: Dict[str, str] = Field(default_factory=lambda: {
        "large": "1.125rem", "default": "1.0rem", "small": "0.875rem", "xsmall": "0.75rem",
    })
    font_weights: Dict[str, int] = Field(default_factory=lambda: {
        "light": 300, "regular": 400, "medium": 500, "semibold": 600, "bold": 700,
    })
    line_heights: Dict[str, str] = Field(default_factory=lambda: {
        "tight": "1.2", "normal": "1.5", "relaxed": "1.75",
    })
    letter_spacing: Dict[str, str] = Field(default_factory=lambda: {
        "tight": "-0.025em", "normal": "0em", "wide": "0.025em", "wider": "0.05em",
    })
    heading_line_height: str = "1.2"
    body_line_height: str = "1.6"

    model_config = ConfigDict(from_attributes=True)


class BlueprintTheme(BaseModel):
    color_palette: BlueprintColorPalette = Field(default_factory=BlueprintColorPalette)
    typography: BlueprintTypography = Field(default_factory=BlueprintTypography)
    dark_mode: bool = False
    visual_style: str = "modern-saas"
    ui_personality: str = "clean"
    button_style: str = "rounded-lg"
    card_style: str = "elevated"
    form_style: str = "standard"
    icon_style: str = "outline"
    border_radius: str = "8px"
    shadow: str = "0 1px 3px rgba(0,0,0,0.1)"
    transition_duration: str = "200ms"
    spacing_scale: str = "default"
    container_width: str = "1200px"

    model_config = ConfigDict(from_attributes=True)


class BlueprintComponent(BaseModel):
    component_name: str
    component_type: str = ""
    section_type: str = ""
    title: Optional[str] = None
    description: Optional[str] = None
    display_order: int = 0
    variant: str = "default"
    layout: str = "default"
    size: str = "medium"
    icon: Optional[str] = None
    image: Optional[str] = None
    visible: bool = True
    required: bool = True
    count: int = 1
    confidence: int = 100
    props: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class BlueprintAnimation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    animation_type: str = "fade-in-up"
    target_component: str
    duration_ms: int = 500
    delay_ms: int = 0
    easing: str = "ease-out"
    trigger: str = "on-scroll"
    enabled: bool = True
    priority: str = "medium"

    model_config = ConfigDict(from_attributes=True)


class BlueprintAnimationList(BaseModel):
    animations: List[BlueprintAnimation] = Field(default_factory=list)
    with_animation: bool = True
    support_reduced_motion: bool = True
    default_animation_level: str = "medium"

    model_config = ConfigDict(from_attributes=True)


class BlueprintOpenGraph(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    image: Optional[str] = None
    site_name: Optional[str] = None
    url: Optional[str] = None
    type: str = "website"

    model_config = ConfigDict(from_attributes=True)


class BlueprintTwitterCard(BaseModel):
    card_type: str = "summary_large_image"
    title: Optional[str] = None
    description: Optional[str] = None
    image: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class BlueprintStructuredData(BaseModel):
    schema_type: Optional[str] = None
    schema_types: List[str] = Field(default_factory=list)
    organization_name: Optional[str] = None
    organization_logo: Optional[str] = None
    contact_point: Optional[Dict[str, str]] = None
    same_as: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class BlueprintHeadingBlueprint(BaseModel):
    expected_h1_count: int = 1
    expected_h2_range: List[int] = Field(default_factory=lambda: [2, 8])
    expected_h3_range: List[int] = Field(default_factory=lambda: [0, 12])
    h1_suggestions: List[str] = Field(default_factory=list)
    h2_suggestions: List[str] = Field(default_factory=list)
    hierarchy_required: bool = True

    model_config = ConfigDict(from_attributes=True)


class BlueprintImageBlueprint(BaseModel):
    alt_text_required: bool = True
    lazy_loading: bool = True
    responsive_images: bool = True
    webp_preferred: bool = True
    svg_for_icons: bool = True
    image_formats: List[str] = Field(default_factory=lambda: ["webp", "avif", "png", "jpg"])

    model_config = ConfigDict(from_attributes=True)


class BlueprintSEO(BaseModel):
    page_title: Optional[str] = None
    page_title_template: Optional[str] = None
    meta_description: Optional[str] = None
    meta_description_template: Optional[str] = None
    meta_keywords: List[str] = Field(default_factory=list)
    focus_keywords: List[str] = Field(default_factory=list)
    canonical_url: Optional[str] = None
    canonical_url_template: Optional[str] = None
    robots_policy: str = "index,follow"
    open_graph: BlueprintOpenGraph = Field(default_factory=BlueprintOpenGraph)
    twitter_card: BlueprintTwitterCard = Field(default_factory=BlueprintTwitterCard)
    schema_markup: BlueprintStructuredData = Field(default_factory=BlueprintStructuredData)
    language: str = "en"
    hreflang: Optional[str] = None
    favicon_required: bool = True
    sitemap_required: bool = True
    robots_txt_required: bool = True

    model_config = ConfigDict(from_attributes=True)


class BlueprintPerformance(BaseModel):
    target_lighthouse_score: int = 90
    target_pagespeed_score: int = 85
    target_fcp: str = "1.8s"
    target_lcp: str = "2.5s"
    target_cls: float = 0.1
    target_tbt: str = "200ms"
    target_inp: str = "200ms"
    image_optimization: bool = True
    code_splitting: bool = True
    dynamic_imports: bool = True
    font_preloading: bool = True
    script_strategy: str = "defer"
    prefetch_required: bool = False
    preconnect_required: bool = True
    dns_prefetch_required: bool = True

    model_config = ConfigDict(from_attributes=True)


class BlueprintAccessibility(BaseModel):
    wcag_target: str = "AA"
    semantic_html_required: bool = True
    aria_labels_required: bool = True
    keyboard_navigation: bool = True
    focus_states: bool = True
    color_contrast: bool = True
    skip_navigation: bool = True
    screen_reader_support: bool = True
    form_validation_labels: bool = True
    button_accessibility: bool = True

    model_config = ConfigDict(from_attributes=True)


class BlueprintMobile(BaseModel):
    responsive: bool = True
    mobile_first: bool = True
    tablet_breakpoint: str = "768px"
    desktop_breakpoint: str = "1024px"
    touch_friendly: bool = True
    minimum_tap_size: str = "44px"
    sticky_mobile_navigation: bool = True

    model_config = ConfigDict(from_attributes=True)


class BlueprintAssets(BaseModel):
    logo_required: bool = True
    favicon_required: bool = True
    hero_image_required: bool = True
    service_images_required: bool = True
    team_photos_required: bool = False
    portfolio_images_required: bool = False
    testimonial_avatars_required: bool = False
    og_image_required: bool = True
    image_specifications: Dict[str, str] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class BlueprintHero(BaseModel):
    layout: str = "centered"
    headline_required: bool = True
    subtitle_required: bool = True
    description_required: bool = False
    cta_primary_required: bool = True
    cta_secondary_required: bool = False
    background_type: str = "image"
    image_position: str = "background"
    height: str = "80vh"
    overlay: bool = True

    model_config = ConfigDict(from_attributes=True)


class BlueprintValidationItem(BaseModel):
    field: str
    message: str
    severity: str = "error"

    model_config = ConfigDict(from_attributes=True)


class BlueprintSummary(BaseModel):
    business_type: str = ""
    website_style: str = ""
    total_sections: int = 0
    total_components: int = 0
    total_assets: int = 0
    animation_count: int = 0
    seo_level: str = "standard"
    accessibility_level: str = "AA"
    performance_target: str = "90"
    estimated_pages: int = 1
    estimated_complexity: str = "medium"
    estimated_ai_tokens: int = 0

    model_config = ConfigDict(from_attributes=True)


class BuilderStatus(BaseModel):
    is_valid: bool = False
    is_ready_for_generation: bool = False
    readiness_score: int = 0
    validation_errors: List[BlueprintValidationItem] = Field(default_factory=list)
    validation_warnings: List[BlueprintValidationItem] = Field(default_factory=list)
    missing_required_sections: List[str] = Field(default_factory=list)
    missing_assets: List[str] = Field(default_factory=list)
    missing_brand_information: List[str] = Field(default_factory=list)
    missing_contact_information: List[str] = Field(default_factory=list)
    missing_navigation: bool = False
    missing_theme: bool = False
    missing_typography: bool = False
    missing_cta: bool = False
    missing_images: List[str] = Field(default_factory=list)
    missing_seo: bool = False

    model_config = ConfigDict(from_attributes=True)


class WebsiteBlueprint(BaseModel):
    project_name: Optional[str] = None
    brand_name: Optional[str] = None
    business_category: Optional[str] = None
    industry: Optional[str] = None
    website_style: str = "modern-saas"
    visual_style: str = "modern-saas"
    ui_personality: str = "clean"

    color_palette: BlueprintColorPalette = Field(default_factory=BlueprintColorPalette)
    typography: BlueprintTypography = Field(default_factory=BlueprintTypography)
    theme: BlueprintTheme = Field(default_factory=BlueprintTheme)

    layout: BlueprintLayout = Field(default_factory=BlueprintLayout)
    navigation: BlueprintNavigation = Field(default_factory=BlueprintNavigation)
    footer: BlueprintFooter = Field(default_factory=BlueprintFooter)

    hero: BlueprintHero = Field(default_factory=BlueprintHero)
    about: Optional[BlueprintSection] = None
    services: Optional[BlueprintSection] = None
    products: Optional[BlueprintSection] = None
    portfolio: Optional[BlueprintSection] = None
    pricing: Optional[BlueprintSection] = None
    testimonials: Optional[BlueprintSection] = None
    faq: Optional[BlueprintSection] = None
    team: Optional[BlueprintSection] = None
    contact: Optional[BlueprintSection] = None

    seo: BlueprintSEO = Field(default_factory=BlueprintSEO)
    heading_blueprint: BlueprintHeadingBlueprint = Field(default_factory=BlueprintHeadingBlueprint)
    image_blueprint: BlueprintImageBlueprint = Field(default_factory=BlueprintImageBlueprint)
    performance: BlueprintPerformance = Field(default_factory=BlueprintPerformance)
    accessibility: BlueprintAccessibility = Field(default_factory=BlueprintAccessibility)
    mobile: BlueprintMobile = Field(default_factory=BlueprintMobile)
    assets: BlueprintAssets = Field(default_factory=BlueprintAssets)

    animations: BlueprintAnimationList = Field(default_factory=BlueprintAnimationList)
    required_components: List[BlueprintComponent] = Field(default_factory=list)

    sections: List[BlueprintSection] = Field(default_factory=list)
    missing_sections: List[str] = Field(default_factory=list)
    recommended_sections: List[Dict[str, str]] = Field(default_factory=list)

    generation_priority: int = 5
    estimated_complexity: str = "medium"
    created_at: datetime = Field(default_factory=datetime.utcnow)

    summary: BlueprintSummary = Field(default_factory=BlueprintSummary)
    builder_status: BuilderStatus = Field(default_factory=BuilderStatus)

    model_config = ConfigDict(from_attributes=True)
