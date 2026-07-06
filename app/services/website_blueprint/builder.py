import importlib.util
import json
import re
from typing import Any, Dict, List, Optional, Tuple

_spec = importlib.util.spec_from_file_location("_wi_schemas", "app/services/website_intelligence/schemas.py")
_wi_schemas = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_wi_schemas)
WebsiteProfile = _wi_schemas.WebsiteProfile

from .constants import (
    ACCESSIBILITY_TARGETS,
    ANIMATION_SUGGESTIONS,
    ANIMATION_TYPES,
    ANIMATION_TRIGGERS,
    ASSET_TYPE_MAP,
    COMPLEXITY_LEVELS,
    COMPONENT_ANIMATION_DEFAULTS,
    COMPONENT_DEFINITIONS,
    COMPONENT_REQUIREMENTS,
    CONTAINER_WIDTHS,
    INDUSTRY_RECOMMENDED_SECTIONS,
    INDUSTRY_UI_PERSONALITY_MAP,
    INDUSTRY_VISUAL_STYLE_MAP,
    LAYOUT_RECOMMENDATIONS,
    PERFORMANCE_TARGETS_BY_STYLE,
    RECOMMENDED_SECTION_REASONS,
    REQUIRED_SECTIONS,
    SCHEMA_ORG_NAMES,
    SCHEMA_TYPE_MAP,
    SECTION_DISPLAY_NAMES,
    SECTION_HEADING_SUGGESTIONS,
    SECTION_IMAGE_REQUIREMENTS,
    SECTION_PRIORITIES,
    STANDARD_SECTIONS,
    VALID_HEX_COLOR_RE,
    VISUAL_STYLE_ANIMATION_LEVEL_MAP,
    WEBSITE_STYLE_THEME_PRESETS,
)
from .helpers import (
    estimate_complexity,
)
from .schemas import (
    BlueprintAccessibility,
    BlueprintAnimation,
    BlueprintAnimationList,
    BlueprintAssets,
    BlueprintColorPalette,
    BlueprintComponent,
    BlueprintFooter,
    BlueprintHeadingBlueprint,
    BlueprintHero,
    BlueprintImageBlueprint,
    BlueprintLayout,
    BlueprintMobile,
    BlueprintNavigation,
    BlueprintOpenGraph,
    BlueprintPerformance,
    BlueprintSEO,
    BlueprintSection,
    BlueprintStructuredData,
    BlueprintSummary,
    BlueprintTheme,
    BlueprintTypography,
    BlueprintTwitterCard,
    BlueprintValidationItem,
    BuilderStatus,
    WebsiteBlueprint,
)
from app.services.website_intelligence.schemas import WebsiteProfile


def _detect_industry(business: Any, company: Any) -> str:
    for src in (business, company):
        if src:
            for field in ("industry", "category", "business_type"):
                val = getattr(src, field, None)
                if val:
                    return val.lower().strip()
    return ""


def _normalize(val: str) -> str:
    return val.lower().replace(" ", "_").replace("-", "_").replace("'", "")


def _detect_visual_style(industry: str) -> str:
    if not industry:
        return "modern-saas"
    for key, style in INDUSTRY_VISUAL_STYLE_MAP.items():
        if key in industry:
            return style
    return "modern-saas"


def _detect_ui_personality(industry: str) -> str:
    if not industry:
        return "clean"
    for key, personality in INDUSTRY_UI_PERSONALITY_MAP.items():
        if key in industry:
            return personality
    return "clean"


def _build_theme(
    palette: BlueprintColorPalette,
    typography: BlueprintTypography,
    visual_style: str,
    industry: str,
) -> BlueprintTheme:
    preset = WEBSITE_STYLE_THEME_PRESETS.get(visual_style, WEBSITE_STYLE_THEME_PRESETS["modern-saas"])
    dark_mode = bool(
        palette.background
        and palette.background.lower() in ("#0f172a", "#000000", "#111827", "#1e293b")
    )
    if visual_style == "technology":
        dark_mode = True

    container_val = CONTAINER_WIDTHS.get(preset.get("container_width", "default"), "1200px")

    return BlueprintTheme(
        color_palette=palette,
        typography=typography,
        dark_mode=dark_mode,
        visual_style=preset.get("visual_style", "modern-saas"),
        ui_personality=preset.get("ui_personality", "clean"),
        button_style=preset.get("button_style", "rounded-lg"),
        card_style=preset.get("card_style", "elevated"),
        form_style=preset.get("form_style", "standard"),
        icon_style=preset.get("icon_style", "outline"),
        border_radius=preset.get("border_radius", "8px"),
        shadow=preset.get("shadow", "0 1px 3px rgba(0,0,0,0.1)"),
        transition_duration=preset.get("transition_duration", "200ms"),
        spacing_scale=preset.get("spacing_scale", "default"),
        container_width=container_val,
    )


def _build_seo_blueprint(
    brand_name: str,
    industry: str,
    visual_style: str,
    profile: Any,
    detected_section_types: Dict[str, Any],
) -> BlueprintSEO:
    seo_src = profile.seo
    business = profile.business
    company = profile.company

    page_title = getattr(seo_src, "page_title", None)
    if not page_title:
        page_title = brand_name

    meta_description = getattr(seo_src, "meta_description", None)
    if not meta_description:
        if company and company.description:
            meta_description = company.description[:160]
        else:
            meta_description = f"{brand_name} — Professional website"

    meta_keywords = getattr(seo_src, "focus_keywords", [])
    focus_keywords = list(meta_keywords)

    language = "en"
    hreflang = None
    if company and company.language:
        language = company.language
    if language != "en":
        hreflang = language

    clean_name = brand_name.lower().replace(" ", "").replace("'", "") if brand_name else ""
    canonical_url = f"https://{clean_name}.com" if clean_name else None

    robots_policy = "index,follow"

    schema_type = SCHEMA_ORG_NAMES.get(industry, "Organization")
    schema_types = SCHEMA_TYPE_MAP.get(industry, ["Organization"])

    org_name = brand_name
    org_logo = None
    if business:
        org_logo = getattr(business, "logo_url", None)

    same_as = []
    if profile.social_links:
        same_as = list(profile.social_links)

    open_graph = BlueprintOpenGraph(
        title=page_title,
        description=meta_description[:160] if meta_description else None,
        site_name=brand_name,
        url=canonical_url,
        type="website",
    )

    twitter_card = BlueprintTwitterCard(
        card_type="summary_large_image",
        title=page_title,
        description=meta_description[:160] if meta_description else None,
    )

    schema_markup = BlueprintStructuredData(
        schema_type=schema_type,
        schema_types=schema_types,
        organization_name=org_name,
        organization_logo=org_logo,
        same_as=same_as,
    )

    return BlueprintSEO(
        page_title=page_title,
        page_title_template=f"{{page_title}} | {brand_name}" if brand_name else None,
        meta_description=meta_description,
        meta_description_template=meta_description[:140] + "..." if meta_description and len(meta_description) > 140 else meta_description,
        meta_keywords=meta_keywords,
        focus_keywords=focus_keywords,
        canonical_url=canonical_url,
        canonical_url_template=f"https://{clean_name}.com/{{slug}}" if clean_name else None,
        robots_policy=robots_policy,
        open_graph=open_graph,
        twitter_card=twitter_card,
        schema_markup=schema_markup,
        language=language,
        hreflang=hreflang,
        favicon_required=not bool(getattr(business, "favicon", None)),
        sitemap_required=True,
        robots_txt_required=True,
    )


def _build_heading_blueprint(
    brand_name: str,
    detected_section_types: Dict[str, Any],
) -> BlueprintHeadingBlueprint:
    h1_suggestions: List[str] = []
    h2_suggestions: List[str] = []

    for sec_type in ("hero", "about", "services", "features", "why_choose_us",
                     "portfolio", "pricing", "testimonials", "faq", "team", "contact"):
        if sec_type in detected_section_types:
            hints = SECTION_HEADING_SUGGESTIONS.get(sec_type, {})
            for h1 in hints.get("h1", []):
                suggestion = h1.replace("{brand_name}", brand_name) if brand_name else h1
                if suggestion not in h1_suggestions:
                    h1_suggestions.append(suggestion)
            for h2 in hints.get("h2", []):
                suggestion = h2.replace("{brand_name}", brand_name) if brand_name else h2
                if suggestion not in h2_suggestions:
                    h2_suggestions.append(suggestion)

    detected_count = len(detected_section_types)
    expected_h2_min = max(2, detected_count - 1)
    expected_h2_max = detected_count * 2 + 2

    return BlueprintHeadingBlueprint(
        expected_h1_count=1,
        expected_h2_range=[expected_h2_min, expected_h2_max],
        expected_h3_range=[0, max(12, detected_count * 3)],
        h1_suggestions=h1_suggestions[:3],
        h2_suggestions=h2_suggestions[:10],
        hierarchy_required=True,
    )


def _build_image_blueprint() -> BlueprintImageBlueprint:
    return BlueprintImageBlueprint(
        alt_text_required=True,
        lazy_loading=True,
        responsive_images=True,
        webp_preferred=True,
        svg_for_icons=True,
        image_formats=["webp", "avif", "png", "jpg"],
    )


def _build_performance_blueprint(visual_style: str) -> BlueprintPerformance:
    targets = PERFORMANCE_TARGETS_BY_STYLE.get(visual_style, PERFORMANCE_TARGETS_BY_STYLE["modern-saas"])
    return BlueprintPerformance(
        target_lighthouse_score=targets["target_lighthouse_score"],
        target_pagespeed_score=targets["target_pagespeed_score"],
        target_fcp=targets["target_fcp"],
        target_lcp=targets["target_lcp"],
        target_cls=targets["target_cls"],
        target_tbt=targets["target_tbt"],
        target_inp=targets["target_inp"],
        image_optimization=targets["image_optimization"],
        code_splitting=targets["code_splitting"],
        dynamic_imports=targets["dynamic_imports"],
        font_preloading=targets["font_preloading"],
        script_strategy=targets["script_strategy"],
        prefetch_required=targets["prefetch_required"],
        preconnect_required=targets["preconnect_required"],
        dns_prefetch_required=targets["dns_prefetch_required"],
    )


def _build_accessibility_blueprint(visual_style: str) -> BlueprintAccessibility:
    a11y = ACCESSIBILITY_TARGETS.get(visual_style, ACCESSIBILITY_TARGETS["modern-saas"])
    return BlueprintAccessibility(
        wcag_target=a11y["wcag_target"],
        semantic_html_required=True,
        aria_labels_required=True,
        keyboard_navigation=True,
        focus_states=True,
        color_contrast=a11y["color_contrast"],
        skip_navigation=True,
        screen_reader_support=True,
        form_validation_labels=True,
        button_accessibility=True,
    )


def _build_mobile_blueprint(visual_style: str) -> BlueprintMobile:
    return BlueprintMobile(
        responsive=True,
        mobile_first=True,
        tablet_breakpoint="768px",
        desktop_breakpoint="1024px",
        touch_friendly=True,
        minimum_tap_size="44px",
        sticky_mobile_navigation=visual_style not in ("minimal", "portfolio"),
    )


def _build_section(
    section_type: str,
    order: int,
    heading: Optional[str] = None,
    subheading: Optional[str] = None,
    description: Optional[str] = None,
    required: bool = True,
    confidence: int = 100,
) -> BlueprintSection:
    rec = LAYOUT_RECOMMENDATIONS.get(section_type, {})
    display_name = SECTION_DISPLAY_NAMES.get(section_type, section_type.replace("_", " ").title())
    columns = int(rec.get("columns", "1"))
    layout = rec.get("layout", "default")
    priority = SECTION_PRIORITIES.get(section_type, 10)
    return BlueprintSection(
        section_type=section_type,
        display_name=display_name,
        order=order,
        required=required,
        layout=layout,
        columns=columns,
        heading=heading,
        subheading=subheading,
        description=description,
        priority=priority,
        confidence=confidence,
    )


def _pick_variant(
    component_name: str,
    section_data: Any,
    hero_layout: Optional[str] = None,
    columns: int = 1,
) -> str:
    definition = COMPONENT_DEFINITIONS.get(component_name, {})
    variants = definition.get("variants", ["default"])
    if "default" in variants and len(variants) == 1:
        return "default"

    if component_name == "Navbar":
        if section_data and hasattr(section_data, "style"):
            style = getattr(section_data, "style", "solid")
            if style in variants:
                return style
        return "sticky" if "sticky" in variants else variants[0]

    if component_name == "HeroSection":
        if hero_layout and hero_layout in variants:
            return hero_layout
        if hero_layout:
            if hero_layout == "image-left":
                return "split"
            if hero_layout == "image-right":
                return "split"
            if hero_layout == "centered":
                return "centered"
            if hero_layout == "text-only":
                return "minimal"
        return variants[0]

    if component_name == "HeroImage":
        if hero_layout == "image-left":
            return "left-side"
        if hero_layout == "image-right":
            return "right-side"
        if hero_layout == "background":
            return "background"
        return "mockup" if "mockup" in variants else variants[0]

    if component_name in ("ServiceCard", "FeatureCard", "PricingCard", "PortfolioCard", "TeamCard", "TestimonialCard", "ProductCard", "BlogCard"):
        if columns >= 3:
            return "minimal" if "minimal" in variants else variants[0]
        if columns == 1:
            return "detailed" if "detailed" in variants else variants[0]
        return variants[0]

    if component_name == "PricingCard":
        if columns >= 3:
            return "comparison" if "comparison" in variants else "featured" if "featured" in variants else variants[0]
        return "simple" if "simple" in variants else variants[0]

    if component_name == "FooterColumns":
        col_map = {2: "2-columns", 3: "3-columns", 4: "4-columns", 5: "5-columns"}
        for c, v in col_map.items():
            if columns >= c and v in variants:
                return v
        return variants[0]

    return variants[0]


def _pick_layout(
    component_name: str,
    section_data: Any,
    columns: int = 1,
) -> str:
    definition = COMPONENT_DEFINITIONS.get(component_name, {})
    layouts = definition.get("layouts", ["default"])
    if columns >= 3 and "grid" in layouts:
        return "grid"
    if columns == 2 and "two-column" in layouts:
        return "two-column"
    if columns == 1 and "single-column" in layouts:
        return "single-column"
    if "full-width" in layouts:
        return "full-width"
    if "container" in layouts:
        return "container"
    return layouts[0]


def _get_component_image(component_name: str, section_type: str) -> Optional[str]:
    if component_name in ("HeroSection", "HeroImage", "HeroVideo"):
        return "hero"
    if component_name in ("ServiceCard", "FeatureCard"):
        return "icon"
    if component_name in ("ProductCard",):
        return "product"
    if component_name in ("PortfolioCard", "CaseStudyCard", "GalleryGrid"):
        return "portfolio"
    if component_name in ("TeamCard", "Avatar"):
        return "team"
    if component_name in ("TestimonialCard",):
        return "testimonial"
    if component_name in ("BlogCard",):
        return "blog"
    if component_name in ("Logo",):
        return "logo"
    return None


def _generate_components(
    detected_section_types: Dict[str, BlueprintSection],
    recommended_sections: List[Dict[str, str]],
    hero_layout: Optional[str] = None,
    footer_columns: int = 4,
) -> List[BlueprintComponent]:
    components: List[BlueprintComponent] = []
    used_ids: set = set()
    order = 0

    section_order = ["navigation", "hero", "about", "services", "features", "products",
                     "why_choose_us", "portfolio", "pricing", "testimonials", "faq",
                     "team", "blog", "contact", "footer"]

    processed_sections: set = set()

    def add_component(
        component_name: str,
        section_type: str,
        variant: Optional[str] = None,
        layout: Optional[str] = None,
        count: int = 1,
        required: bool = True,
        confidence: int = 100,
        visible: bool = True,
    ) -> None:
        nonlocal order
        definition = COMPONENT_DEFINITIONS.get(component_name, {})
        comp_section = definition.get("type", section_type)
        comp_variant = variant or _pick_variant(component_name, None, hero_layout)
        comp_layout = layout or _pick_layout(component_name, None)
        comp_desc = definition.get("description", "")
        comp_sizes = definition.get("sizes", ["medium"])
        comp_size = comp_sizes[0] if comp_sizes else "medium"

        assets_needed = ASSET_TYPE_MAP.get(component_name, [])
        comp_image = _get_component_image(component_name, section_type)

        order += 1

        components.append(BlueprintComponent(
            component_name=component_name,
            component_type=comp_section,
            section_type=section_type,
            title=component_name,
            description=comp_desc,
            display_order=order,
            variant=comp_variant,
            layout=comp_layout,
            size=comp_size,
            visible=visible,
            required=required,
            count=count,
            confidence=confidence,
        ))

    for sec_type in section_order:
        if sec_type in processed_sections:
            continue

        if sec_type == "navigation" and sec_type in detected_section_types:
            add_component("Navbar", "navigation", count=1)
            add_component("Logo", "navigation", count=1)
            add_component("NavigationLink", "navigation", count=5)
            cta_variant = "cta" if "cta" in COMPONENT_DEFINITIONS.get("Button", {}).get("variants", []) else "primary"
            nav_section = detected_section_types.get("navigation")
            if nav_section:
                add_component("Button", "navigation", variant=cta_variant, count=1)
            add_component("Dropdown", "navigation", count=2, confidence=70)
            processed_sections.add("navigation")

        elif sec_type == "hero" and sec_type in detected_section_types:
            add_component("HeroSection", "hero", variant=_pick_variant("HeroSection", None, hero_layout), count=1)
            if hero_layout and hero_layout != "text-only":
                add_component("HeroImage", "hero", variant=_pick_variant("HeroImage", None, hero_layout), count=1)
            add_component("HeroCTA", "hero", count=1)
            add_component("SectionHeader", "hero", count=1, confidence=80)
            processed_sections.add("hero")

        elif sec_type == "about" and sec_type in detected_section_types:
            add_component("SectionHeader", "about", count=1)
            add_component("ImageWithText", "about", variant="image-left" if "image-left" in COMPONENT_DEFINITIONS.get("ImageWithText", {}).get("variants", []) else "split", count=1)
            add_component("StatsCounter", "about", count=3, confidence=60)
            add_component("Timeline", "about", count=1, confidence=50)
            processed_sections.add("about")

        elif sec_type == "services" and sec_type in detected_section_types:
            add_component("SectionHeader", "services", count=1)
            svc_section = detected_section_types.get("services")
            svc_cols = svc_section.columns if svc_section else 3
            add_component("ServiceCard", "services", variant=_pick_variant("ServiceCard", None, columns=svc_cols), count=min(svc_cols, 6), layout=_pick_layout("ServiceCard", None, columns=svc_cols))
            processed_sections.add("services")

        elif sec_type == "features" and sec_type in detected_section_types:
            add_component("SectionHeader", "features", count=1)
            feat_section = detected_section_types.get("features")
            feat_cols = feat_section.columns if feat_section else 3
            add_component("FeatureCard", "features", variant=_pick_variant("FeatureCard", None, columns=feat_cols), count=min(feat_cols * 2, 6), layout=_pick_layout("FeatureCard", None, columns=feat_cols))
            add_component("CheckList", "features", count=1, confidence=60)
            processed_sections.add("features")

        elif sec_type == "products" and sec_type in detected_section_types:
            add_component("SectionHeader", "products", count=1)
            prod_cols = 3
            add_component("ProductCard", "products", variant=_pick_variant("ProductCard", None, columns=prod_cols), count=min(prod_cols * 2, 6), layout=_pick_layout("ProductCard", None, columns=prod_cols))
            processed_sections.add("products")

        elif sec_type == "why_choose_us" and sec_type in detected_section_types:
            add_component("SectionHeader", "why_choose_us", count=1)
            add_component("FeatureCard", "why_choose_us", variant="icon-top" if "icon-top" in COMPONENT_DEFINITIONS.get("FeatureCard", {}).get("variants", []) else "default", count=4)
            add_component("StatsCounter", "why_choose_us", count=3, confidence=70)
            processed_sections.add("why_choose_us")

        elif sec_type == "portfolio" and sec_type in detected_section_types:
            add_component("SectionHeader", "portfolio", count=1)
            add_component("FilterTabs", "portfolio", count=1)
            port_cols = 3
            add_component("PortfolioCard", "portfolio", variant=_pick_variant("PortfolioCard", None, columns=port_cols), count=min(port_cols * 2, 6), layout=_pick_layout("PortfolioCard", None, columns=port_cols))
            add_component("Lightbox", "portfolio", count=1, confidence=70)
            processed_sections.add("portfolio")

        elif sec_type == "pricing" and sec_type in detected_section_types:
            add_component("SectionHeader", "pricing", count=1)
            price_cols = 3
            add_component("PricingCard", "pricing", variant=_pick_variant("PricingCard", None, columns=price_cols), count=price_cols, layout=_pick_layout("PricingCard", None, columns=price_cols))
            add_component("Badge", "pricing", variant="pill" if "pill" in COMPONENT_DEFINITIONS.get("Badge", {}).get("variants", []) else "default", count=1, confidence=60)
            processed_sections.add("pricing")

        elif sec_type == "testimonials" and sec_type in detected_section_types:
            add_component("SectionHeader", "testimonials", count=1)
            add_component("TestimonialCard", "testimonials", variant=_pick_variant("TestimonialCard", None, columns=3), count=3, layout="carousel")
            add_component("StarRating", "testimonials", count=3)
            add_component("Carousel", "testimonials", variant="slide" if "slide" in COMPONENT_DEFINITIONS.get("Carousel", {}).get("variants", []) else "fade", count=1)
            processed_sections.add("testimonials")

        elif sec_type == "faq" and sec_type in detected_section_types:
            add_component("SectionHeader", "faq", count=1)
            add_component("FAQAccordion", "faq", variant="accordion" if "accordion" in COMPONENT_DEFINITIONS.get("FAQAccordion", {}).get("variants", []) else "default", count=1)
            add_component("Accordion", "faq", count=1, confidence=60)
            processed_sections.add("faq")

        elif sec_type == "team" and sec_type in detected_section_types:
            add_component("SectionHeader", "team", count=1)
            team_cols = 4
            add_component("TeamCard", "team", variant=_pick_variant("TeamCard", None, columns=team_cols), count=min(team_cols, 4), layout=_pick_layout("TeamCard", None, columns=team_cols))
            add_component("BioModal", "team", count=1, confidence=60)
            processed_sections.add("team")

        elif sec_type == "blog" and sec_type in detected_section_types:
            add_component("SectionHeader", "blog", count=1)
            add_component("BlogCard", "blog", count=3, layout="grid")
            processed_sections.add("blog")

        elif sec_type == "contact" and sec_type in detected_section_types:
            add_component("SectionHeader", "contact", count=1)
            add_component("ContactForm", "contact", variant="detailed" if "detailed" in COMPONENT_DEFINITIONS.get("ContactForm", {}).get("variants", []) else "simple", count=1)
            add_component("ContactInfoCard", "contact", count=1)
            add_component("GoogleMap", "contact", count=1, confidence=60)
            processed_sections.add("contact")

        elif sec_type == "footer" and sec_type in detected_section_types:
            add_component("FooterColumns", "footer", variant=_pick_variant("FooterColumns", None, columns=footer_columns), count=1, layout="multi-column")
            add_component("Logo", "footer", variant="image" if "image" in COMPONENT_DEFINITIONS.get("Logo", {}).get("variants", []) else "text", count=1)
            add_component("SocialIcons", "footer", count=1)
            add_component("Copyright", "footer", variant=_pick_variant("Copyright", None), count=1)
            add_component("NewsletterForm", "footer", count=1, confidence=50)
            add_component("Divider", "footer", count=1, confidence=40)
            processed_sections.add("footer")

    # Components for recommended (missing) sections — add at lower confidence
    rec_section_types = {r["section"] for r in recommended_sections}
    for sec_type in section_order:
        if sec_type in rec_section_types and sec_type not in processed_sections:
            if sec_type == "testimonials":
                add_component("SectionHeader", "testimonials", confidence=60)
                add_component("TestimonialCard", "testimonials", confidence=60, count=3)
            elif sec_type == "faq":
                add_component("SectionHeader", "faq", confidence=60)
                add_component("FAQAccordion", "faq", confidence=60, count=1)
            elif sec_type == "pricing":
                add_component("SectionHeader", "pricing", confidence=60)
                add_component("PricingCard", "pricing", confidence=60, count=3)
            elif sec_type == "portfolio":
                add_component("SectionHeader", "portfolio", confidence=60)
                add_component("PortfolioCard", "portfolio", confidence=60, count=3)
            elif sec_type == "team":
                add_component("SectionHeader", "team", confidence=60)
                add_component("TeamCard", "team", confidence=60, count=4)
            elif sec_type == "blog":
                add_component("SectionHeader", "blog", confidence=60)
                add_component("BlogCard", "blog", confidence=60, count=3)
            elif sec_type == "contact":
                add_component("SectionHeader", "contact", confidence=60)
                add_component("ContactForm", "contact", confidence=60, count=1)
            else:
                add_component("SectionHeader", sec_type, confidence=60)

    return components


class WebsiteBlueprintBuilder:
    def __init__(self) -> None:
        self._blueprint: Optional[WebsiteBlueprint] = None

    async def build(
        self,
        profile: WebsiteProfile,
    ) -> WebsiteBlueprint:
        business = profile.business
        brand = profile.brand
        company = profile.company
        nav_info = profile.navigation_info
        hi = profile.hero_info
        lay = profile.website_layout
        sections_data = lay.sections if lay else []
        contact = profile.contact
        fi = lay.footer_info if lay else None

        # --- Identity ---
        project_name = getattr(business, "name", None) or ""
        brand_name = project_name
        business_category = getattr(business, "category", None) or ""
        industry_raw = _detect_industry(business, company)
        industry = industry_raw
        visual_style = _detect_visual_style(industry)
        ui_personality = _detect_ui_personality(industry)

        # --- Color Palette ---
        cp_src = profile.colors
        palette = BlueprintColorPalette(
            primary=getattr(cp_src, "primary", None),
            secondary=getattr(cp_src, "secondary", None),
            accent=getattr(cp_src, "accent", None),
            background=getattr(cp_src, "background", None),
            surface=getattr(cp_src, "surface", None),
            text=getattr(cp_src, "text", None),
            muted=getattr(cp_src, "muted", None),
            success=getattr(cp_src, "success", "#10B981"),
            warning=getattr(cp_src, "warning", "#F59E0B"),
            danger=getattr(cp_src, "danger", "#EF4444"),
            info=getattr(cp_src, "info", "#3B82F6"),
        )

        # --- Typography ---
        tp_src = profile.typography
        typography = BlueprintTypography(
            heading_font=getattr(tp_src, "heading_h1", None) or getattr(tp_src, "heading_h2", None) or getattr(tp_src, "heading_h3", None),
            body_font=getattr(tp_src, "body", None),
        )
        if not typography.heading_font and tp_src and tp_src.fonts:
            for f in tp_src.fonts:
                if f.usage and "heading" in f.usage.lower():
                    typography.heading_font = f.family
                    break
        if not typography.body_font and tp_src and tp_src.fonts:
            for f in tp_src.fonts:
                if f.usage and "body" in f.usage.lower():
                    typography.body_font = f.family
                    break
        # Detect secondary font from remaining fonts
        if tp_src and tp_src.fonts:
            used = {typography.heading_font, typography.body_font}
            for f in tp_src.fonts:
                if f.family not in used:
                    typography.secondary_font = f.family
                    break

        # --- Determine header type ---
        is_sticky = nav_info.is_sticky if nav_info else False
        hero_layout = hi.hero_layout if hi else None
        header_type = "solid"
        if is_sticky and hero_layout:
            if hero_layout in ("image-left", "image-right", "split"):
                header_type = "split"
            elif hero_layout == "centered":
                header_type = "centered"
            else:
                header_type = "sticky"
        elif is_sticky:
            header_type = "sticky"
        elif hero_layout in ("image-left", "image-right"):
            header_type = "split"
        elif hero_layout == "centered":
            header_type = "centered"

        # --- Navigation ---
        primary_links: List[Dict[str, str]] = []
        secondary_links: List[Dict[str, str]] = []
        cta_button: Optional[Dict[str, str]] = None
        if nav_info:
            for item in nav_info.primary_nav_items:
                primary_links.append({"label": item.label, "url": item.url})
            for item in nav_info.secondary_nav_items:
                secondary_links.append({"label": item.label, "url": item.url})
        if hi and hi.primary_cta:
            cta_button = {"label": hi.primary_cta.text, "url": hi.primary_cta.url}
        elif profile.call_to_actions:
            first = profile.call_to_actions[0]
            cta_button = {"label": first.text, "url": first.url or "#"}

        navigation = BlueprintNavigation(
            style=header_type,
            sticky=is_sticky or header_type in ("sticky", "centered", "split"),
            primary_links=primary_links,
            secondary_links=secondary_links,
            cta_button=cta_button,
        )

        # --- Footer ---
        footer_cols = 4
        footer_type = "large-multi-column"
        has_business_info = bool(fi and (fi.contact_info or fi.footer_description))
        has_newsletter = bool(fi and fi.newsletter_signup)
        has_social = bool(fi and fi.social_links)
        has_logo = bool(fi and fi.footer_logo)
        if not has_business_info and not has_logo:
            footer_type = "simple"
            footer_cols = 2
        elif has_newsletter:
            footer_type = "large-multi-column"
            footer_cols = 4
        elif has_social and has_logo:
            footer_type = "business"
            footer_cols = 3
        else:
            footer_type = "minimal"
            footer_cols = 1

        footer = BlueprintFooter(
            columns=footer_cols,
            show_logo=has_logo,
            show_description=bool(fi and fi.footer_description),
            show_contact=bool(fi and fi.contact_info),
            show_social=has_social,
            show_newsletter=has_newsletter,
            show_copyright=bool(fi and fi.copyright_text),
            layout=footer_type,
        )

        # --- Hero ---
        hero_bg = "image"
        if hi:
            if hi.background_color and not hi.background_image_url:
                hero_bg = "color"
            elif hi.background_image_url:
                hero_bg = "image"
            elif hi.hero_layout == "text-only":
                hero_bg = "none"
        hero = BlueprintHero(
            layout=hi.hero_layout if hi and hi.hero_layout else "centered",
            headline_required=True,
            subtitle_required=not bool(hi and hi.hero_subtitle),
            description_required=not bool(hi and hi.hero_description),
            cta_primary_required=not bool(hi and hi.primary_cta),
            cta_secondary_required=bool(hi and hi.secondary_cta),
            background_type=hero_bg,
            image_position="background" if hero_bg == "image" else "none",
            height=f"{hi.hero_height}px" if hi and hi.hero_height else "80vh",
            overlay=hero_bg == "image",
        )

        # --- Detect which standard sections are present ---
        detected_section_types: Dict[str, BlueprintSection] = {}
        used_types: set = set()
        order = 0

        def add_if_detected(st: str, heading: Optional[str] = None, sub: Optional[str] = None, desc: Optional[str] = None, required: bool = True, confidence: int = 100):
            nonlocal order
            if st not in used_types:
                used_types.add(st)
                order += 1
                sec = _build_section(st, order, heading=heading, subheading=sub, description=desc, required=required, confidence=confidence)
                detected_section_types[st] = sec
                used_types.add(st)

        add_if_detected("hero", heading=hi.hero_title if hi else None, sub=hi.hero_subtitle if hi else None, desc=hi.hero_description if hi else None)

        if company and company.description:
            add_if_detected("about", heading=company.section_title or "About Us", desc=company.description)

        if profile.services:
            add_if_detected("services", heading="Our Services", desc=f"{len(profile.services)} services detected")

        if profile.products:
            add_if_detected("products", heading="Our Products", desc=f"{len(profile.products)} products detected")

        for sec_data in sections_data:
            st = _normalize(sec_data.section_type)
            if st in ("other", ""):
                continue
            if st == "features":
                add_if_detected("features", heading=sec_data.heading, desc=sec_data.description)
            elif st == "services" and "services" not in used_types:
                add_if_detected("services", heading=sec_data.heading, desc=sec_data.description)
            elif st == "about" and "about" not in used_types:
                add_if_detected("about", heading=sec_data.heading, desc=sec_data.description)
            elif st == "pricing":
                add_if_detected("pricing", heading=sec_data.heading, desc=sec_data.description)
            elif st == "portfolio" or st == "gallery":
                add_if_detected("portfolio", heading=sec_data.heading, desc=sec_data.description)
            elif st == "testimonials":
                add_if_detected("testimonials", heading=sec_data.heading, desc=f"{len(profile.testimonials)} testimonials")
            elif st == "faq":
                add_if_detected("faq", heading=sec_data.heading, desc=f"{len(profile.faqs)} FAQs")
            elif st == "team":
                add_if_detected("team", heading=sec_data.heading, desc=f"{len(profile.team)} team members")
            elif st == "contact":
                add_if_detected("contact", heading=sec_data.heading)
            elif st == "blog" or st == "newsletter":
                add_if_detected("blog" if st == "blog" else "newsletter", heading=sec_data.heading)

        if profile.testimonials and "testimonials" not in used_types:
            add_if_detected("testimonials", heading="Testimonials", desc=f"{len(profile.testimonials)} testimonials")

        if profile.team and "team" not in used_types:
            add_if_detected("team", heading="Our Team", desc=f"{len(profile.team)} team members")

        if profile.faqs and "faq" not in used_types:
            add_if_detected("faq", heading="FAQ", desc=f"{len(profile.faqs)} FAQs")

        contact_detected = bool(contact.emails or contact.phones or contact.address or contact.contact_form_present)
        if contact_detected and "contact" not in used_types:
            add_if_detected("contact", heading="Contact Us")

        if profile.blog_links and "blog" not in used_types:
            add_if_detected("blog", heading="Blog", desc=f"{len(profile.blog_links)} posts")

        add_if_detected("navigation", confidence=100)
        add_if_detected("footer", confidence=100)

        # --- Determine missing sections ---
        standard_keys = [s for s in STANDARD_SECTIONS]
        detected_keys_lower = set(_normalize(k) for k in detected_section_types)
        missing = [s for s in standard_keys if s not in detected_keys_lower and s not in ("navigation", "hero", "footer")]

        # --- Industry-specific section recommendations ---
        industry_recommendations: List[Dict[str, str]] = []
        if industry:
            for ind_key, sections_list in INDUSTRY_RECOMMENDED_SECTIONS.items():
                if ind_key in industry:
                    for rec_sec in sections_list:
                        if rec_sec not in detected_keys_lower:
                            industry_recommendations.append({
                                "section": rec_sec,
                                "reason": RECOMMENDED_SECTION_REASONS.get(rec_sec, f"Recommended for {industry} websites"),
                            })
                    break

        recommended_sections: List[Dict[str, str]] = []
        seen_rec = set()
        for ms in missing:
            if ms not in seen_rec:
                seen_rec.add(ms)
                reason = RECOMMENDED_SECTION_REASONS.get(ms, f"Standard section for business websites")
                recommended_sections.append({"section": ms, "reason": reason})

        for ir in industry_recommendations:
            if ir["section"] not in seen_rec:
                seen_rec.add(ir["section"])
                recommended_sections.append(ir)

        # --- SEO (Phase 2.7e) ---
        seo = _build_seo_blueprint(brand_name, industry, visual_style, profile, detected_section_types)
        heading_blueprint = _build_heading_blueprint(brand_name, detected_section_types)
        image_blueprint = _build_image_blueprint()

        # --- Performance, Accessibility, Mobile (Phase 2.7e) ---
        performance = _build_performance_blueprint(visual_style)
        accessibility = _build_accessibility_blueprint(visual_style)
        mobile = _build_mobile_blueprint(visual_style)

        # --- Assets ---
        has_team_photos = bool(profile.team and any(m.photo_url for m in profile.team))
        has_portfolio_imgs = "portfolio" in detected_keys_lower and any(
            s.images for s in sections_data if _normalize(s.section_type) in ("portfolio", "gallery")
        )
        has_testimonial_avatars = bool(profile.testimonials and any(t.avatar_url for t in profile.testimonials))
        image_specs: Dict[str, str] = {}
        for sec_type in detected_keys_lower:
            if sec_type in SECTION_IMAGE_REQUIREMENTS:
                image_specs[sec_type] = SECTION_IMAGE_REQUIREMENTS[sec_type]

        assets = BlueprintAssets(
            logo_required=not bool(brand and brand.logo_info and brand.logo_info.logo_url),
            favicon_required=not bool(getattr(business, "favicon", None)),
            hero_image_required=hero_bg == "image",
            service_images_required=bool(profile.services) and not all(s.image for s in profile.services if s),
            team_photos_required=not has_team_photos,
            portfolio_images_required=not has_portfolio_imgs,
            testimonial_avatars_required=not has_testimonial_avatars,
            og_image_required=True,
            image_specifications=image_specs,
        )

        # --- Build section list (ordered) ---
        section_order_keys = [s for s in list(detected_section_types)]
        section_order_keys.sort(key=lambda x: SECTION_PRIORITIES.get(x, 50))
        ordered_sections: List[BlueprintSection] = []
        for sk in section_order_keys:
            if sk in detected_section_types:
                ordered_sections.append(detected_section_types[sk])

        seen_ids: set = set()
        for i, sec in enumerate(ordered_sections):
            sec.order = i + 1
            base_id = sec.section_type.replace(" ", "_")
            sec_id = base_id
            counter = 1
            while sec_id in seen_ids:
                counter += 1
                sec_id = f"{base_id}_{counter}"
            seen_ids.add(sec_id)

        # --- Animations (Phase 2.7d) ---
        animation_entries: List[BlueprintAnimation] = []
        used_components: set = set()
        for sec_type, anim_list in ANIMATION_SUGGESTIONS.items():
            if sec_type in detected_keys_lower and sec_type not in ("navigation", "footer"):
                for anim_data in anim_list:
                    element = anim_data["element"]
                    if element not in used_components:
                        used_components.add(element)
                        animation_entries.append(BlueprintAnimation(
                            animation_type=anim_data["animation"],
                            target_component=element,
                            duration_ms=int(anim_data["duration"].replace("ms", "")),
                            delay_ms=int(anim_data["delay"].replace("ms", "")),
                            easing="ease-out",
                            trigger=anim_data.get("trigger", "on-scroll"),
                            priority="medium",
                        ))

        # Add per-component animation defaults from COMPONENT_ANIMATION_DEFAULTS
        for component in components:
            cname = component.component_name
            if cname not in used_components and cname in COMPONENT_ANIMATION_DEFAULTS:
                used_components.add(cname)
                defaults = COMPONENT_ANIMATION_DEFAULTS[cname]
                animation_entries.append(BlueprintAnimation(
                    animation_type=defaults["animation_type"],
                    target_component=cname,
                    duration_ms=defaults["duration_ms"],
                    delay_ms=defaults["delay_ms"],
                    easing=defaults["easing"],
                    trigger=defaults["trigger"],
                    priority=defaults["priority"],
                ))

        visual_style = _detect_visual_style(industry)
        animation_level = VISUAL_STYLE_ANIMATION_LEVEL_MAP.get(visual_style, "medium")
        animations = BlueprintAnimationList(
            animations=animation_entries,
            with_animation=animation_level != "low",
            support_reduced_motion=True,
            default_animation_level=animation_level,
        )

        # --- Components (Phase 2.7c) ---
        components = _generate_components(
            detected_section_types=detected_section_types,
            recommended_sections=recommended_sections,
            hero_layout=hero_layout,
            footer_columns=footer_cols,
        )

        # --- Generation priority and complexity ---
        section_count = len(ordered_sections)
        missing_count = len(missing)
        gen_priority = 5
        if section_count <= 3:
            gen_priority = 8
        elif section_count <= 5:
            gen_priority = 6
        elif missing_count > 4:
            gen_priority = 7

        blueprint = WebsiteBlueprint(
            project_name=project_name,
            brand_name=brand_name,
            business_category=business_category,
            industry=industry,
            website_style="modern-saas",
            color_palette=palette,
            typography=typography,
            visual_style=visual_style,
            ui_personality=ui_personality,
            theme=_build_theme(palette, typography, visual_style, industry),
            layout=BlueprintLayout(),
            navigation=navigation,
            footer=footer,
            hero=hero,
            about=detected_section_types.get("about"),
            services=detected_section_types.get("services"),
            products=detected_section_types.get("products"),
            portfolio=detected_section_types.get("portfolio"),
            pricing=detected_section_types.get("pricing"),
            testimonials=detected_section_types.get("testimonials"),
            faq=detected_section_types.get("faq"),
            team=detected_section_types.get("team"),
            contact=detected_section_types.get("contact"),
            seo=seo,
            heading_blueprint=heading_blueprint,
            image_blueprint=image_blueprint,
            performance=performance,
            accessibility=accessibility,
            mobile=mobile,
            assets=assets,
            animations=animations,
            required_components=components,
            sections=ordered_sections,
            missing_sections=missing,
            recommended_sections=recommended_sections,
            generation_priority=gen_priority,
            estimated_complexity="medium",
            created_at=__import__("datetime").datetime.utcnow(),
        )
        blueprint.estimated_complexity = estimate_complexity(blueprint)
        blueprint.summary = self.generation_summary(blueprint)
        blueprint.builder_status = self.generation_readiness(blueprint)
        self._blueprint = blueprint
        return blueprint

    def validate(self, blueprint: WebsiteBlueprint) -> Tuple[bool, List[BlueprintValidationItem], List[BlueprintValidationItem]]:
        errors: List[BlueprintValidationItem] = []
        warnings: List[BlueprintValidationItem] = []

        hex_re = re.compile(VALID_HEX_COLOR_RE)

        # ── Sections ──
        seen_sections: set = set()
        if not blueprint.sections:
            errors.append(BlueprintValidationItem(field="sections", message="No sections defined", severity="error"))
        for s in blueprint.sections:
            if s.section_type in seen_sections:
                errors.append(BlueprintValidationItem(field=f"sections.{s.section_type}", message="Duplicate section type", severity="error"))
            seen_sections.add(s.section_type)
            if not s.section_type:
                errors.append(BlueprintValidationItem(field="sections", message="Section with empty type", severity="error"))
            if not (0 <= s.confidence <= 100):
                errors.append(BlueprintValidationItem(field=f"sections.{s.section_type}.confidence", message=f"Confidence {s.confidence} out of range", severity="error"))

        # ── Required sections ──
        section_types = {s.section_type for s in blueprint.sections}
        for req in REQUIRED_SECTIONS:
            if req not in section_types:
                errors.append(BlueprintValidationItem(field=f"sections.{req}", message=f"Missing required section: {req}", severity="error"))

        # ── Components ──
        seen_orders: set = set()
        seen_components: set = set()
        if not blueprint.required_components:
            warnings.append(BlueprintValidationItem(field="required_components", message="No components defined", severity="warning"))
        for comp in blueprint.required_components:
            if comp.component_name in seen_components:
                errors.append(BlueprintValidationItem(field=f"components.{comp.component_name}", message="Duplicate component name", severity="error"))
            seen_components.add(comp.component_name)
            if comp.display_order in seen_orders and comp.display_order > 0:
                warnings.append(BlueprintValidationItem(field=f"components.{comp.component_name}.display_order", message=f"Duplicate display_order {comp.display_order}", severity="warning"))
            if comp.display_order > 0:
                seen_orders.add(comp.display_order)
            if comp.component_name not in COMPONENT_DEFINITIONS:
                warnings.append(BlueprintValidationItem(field=f"components.{comp.component_name}", message=f"Unknown component: {comp.component_name}", severity="warning"))
            if comp.section_type and comp.section_type not in section_types:
                warnings.append(BlueprintValidationItem(field=f"components.{comp.component_name}", message=f"Orphan component (section {comp.section_type} not found)", severity="warning"))
            if not (0 <= comp.confidence <= 100):
                errors.append(BlueprintValidationItem(field=f"components.{comp.component_name}.confidence", message=f"Confidence {comp.confidence} out of range", severity="error"))

        # ── Theme & Colors ──
        theme = blueprint.theme
        palette = theme.color_palette
        for color_field in ("primary", "secondary", "accent", "background", "surface", "text", "muted", "success", "warning", "danger", "info"):
            val = getattr(palette, color_field, None)
            if val and not hex_re.match(val):
                errors.append(BlueprintValidationItem(field=f"color_palette.{color_field}", message=f"Invalid hex color: {val}", severity="error"))

        # ── Typography ──
        typ = blueprint.typography
        if typ.heading_font and not typ.heading_font.strip():
            warnings.append(BlueprintValidationItem(field="typography.heading_font", message="Empty heading font", severity="warning"))
        if typ.body_font and not typ.body_font.strip():
            warnings.append(BlueprintValidationItem(field="typography.body_font", message="Empty body font", severity="warning"))

        # ── Animations ──
        for anim in blueprint.animations.animations:
            if anim.animation_type not in ANIMATION_TYPES:
                warnings.append(BlueprintValidationItem(field=f"animations.{anim.id}.animation_type", message=f"Unknown animation type: {anim.animation_type}", severity="warning"))
            if anim.trigger not in ANIMATION_TRIGGERS:
                warnings.append(BlueprintValidationItem(field=f"animations.{anim.id}.trigger", message=f"Unknown trigger: {anim.trigger}", severity="warning"))
            if anim.priority not in ("low", "medium", "high", "critical"):
                warnings.append(BlueprintValidationItem(field=f"animations.{anim.id}.priority", message=f"Unknown priority: {anim.priority}", severity="warning"))

        # ── Navigation ──
        nav = blueprint.navigation
        seen_links = set()
        for link in nav.primary_links:
            label = link.get("label", "")
            if label in seen_links:
                warnings.append(BlueprintValidationItem(field="navigation.primary_links", message=f"Duplicate nav link: {label}", severity="warning"))
            seen_links.add(label)

        # ── SEO ──
        seo = blueprint.seo
        if not seo.page_title:
            warnings.append(BlueprintValidationItem(field="seo.page_title", message="Missing page title", severity="warning"))
        if not seo.meta_description:
            warnings.append(BlueprintValidationItem(field="seo.meta_description", message="Missing meta description", severity="warning"))

        # ── Assets ──
        assets = blueprint.assets
        if assets.logo_required:
            warnings.append(BlueprintValidationItem(field="assets.logo", message="Logo asset required", severity="warning"))
        if assets.hero_image_required:
            warnings.append(BlueprintValidationItem(field="assets.hero_image", message="Hero image asset required", severity="warning"))

        # ── Performance ──
        perf = blueprint.performance
        if not (0 <= perf.target_lighthouse_score <= 100):
            errors.append(BlueprintValidationItem(field="performance.target_lighthouse_score", message=f"Invalid lighthouse score: {perf.target_lighthouse_score}", severity="error"))

        # ── Footer ──
        if blueprint.footer.columns < 1 or blueprint.footer.columns > 6:
            warnings.append(BlueprintValidationItem(field="footer.columns", message=f"Unusual column count: {blueprint.footer.columns}", severity="warning"))

        is_valid = len(errors) == 0
        return is_valid, errors, warnings

    def generation_readiness(self, blueprint: WebsiteBlueprint) -> BuilderStatus:
        is_valid, errors, warnings = self.validate(blueprint)
        section_types = {s.section_type for s in blueprint.sections}

        # Missing required sections
        missing_required = [r for r in REQUIRED_SECTIONS if r not in section_types]

        # Missing brand info
        missing_brand: List[str] = []
        if not blueprint.brand_name:
            missing_brand.append("brand_name")

        # Missing contact info
        missing_contact: List[str] = []

        # Missing navigation
        missing_nav = not blueprint.navigation.primary_links and not blueprint.navigation.secondary_links

        # Missing theme
        missing_thm = not blueprint.theme.color_palette.primary

        # Missing typography
        missing_type = not blueprint.typography.heading_font or not blueprint.typography.body_font

        # Missing CTA
        missing_cta = blueprint.navigation.cta_button is None

        # Missing images / assets
        missing_imgs: List[str] = []
        if blueprint.assets.logo_required:
            missing_imgs.append("logo")
        if blueprint.assets.hero_image_required:
            missing_imgs.append("hero_image")
        if blueprint.assets.service_images_required:
            missing_imgs.append("service_images")

        # Missing SEO
        missing_seo = not blueprint.seo.page_title or not blueprint.seo.meta_description

        # Missing assets (from assets config)
        missing_asset_list: List[str] = []
        if blueprint.assets.logo_required:
            missing_asset_list.append("logo")
        if blueprint.assets.favicon_required:
            missing_asset_list.append("favicon")

        # ── Readiness score ──
        score = 100
        deductions = {
            "errors": len(errors) * 15,
            "warnings": len(warnings) * 5,
            "missing_required_sections": len(missing_required) * 15,
            "missing_brand": len(missing_brand) * 10,
            "missing_contact": len(missing_contact) * 5,
            "missing_nav": 10 if missing_nav else 0,
            "missing_theme": 10 if missing_thm else 0,
            "missing_typography": 10 if missing_type else 0,
            "missing_cta": 5 if missing_cta else 0,
            "missing_seo": 10 if missing_seo else 0,
            "missing_images": len(missing_imgs) * 5,
        }
        for deduction in deductions.values():
            score -= deduction
        readiness_score = max(0, min(100, score))

        return BuilderStatus(
            is_valid=is_valid,
            is_ready_for_generation=readiness_score >= 70,
            readiness_score=readiness_score,
            validation_errors=errors,
            validation_warnings=warnings,
            missing_required_sections=missing_required,
            missing_assets=missing_asset_list,
            missing_brand_information=missing_brand,
            missing_contact_information=missing_contact,
            missing_navigation=missing_nav,
            missing_theme=missing_thm,
            missing_typography=missing_type,
            missing_cta=missing_cta,
            missing_images=missing_imgs,
            missing_seo=missing_seo,
        )

    def generation_summary(self, blueprint: WebsiteBlueprint) -> BlueprintSummary:
        section_count = len(blueprint.sections)
        component_count = len(blueprint.required_components)
        animation_count = len(blueprint.animations.animations)

        # Asset count
        asset_count = 0
        if blueprint.assets.logo_required:
            asset_count += 1
        if blueprint.assets.favicon_required:
            asset_count += 1
        if blueprint.assets.hero_image_required:
            asset_count += 1
        if blueprint.assets.service_images_required:
            asset_count += 1
        if blueprint.assets.team_photos_required:
            asset_count += 1
        if blueprint.assets.portfolio_images_required:
            asset_count += 1
        if blueprint.assets.testimonial_avatars_required:
            asset_count += 1
        if blueprint.assets.og_image_required:
            asset_count += 1

        # Complexity
        complexity = blueprint.estimated_complexity
        if complexity not in COMPLEXITY_LEVELS:
            # Determine complexity from section count
            for level_key, cfg in COMPLEXITY_LEVELS.items():
                r = cfg["section_range"]
                if r[0] <= section_count <= r[1]:
                    complexity = level_key
                    break
            else:
                complexity = "large"

        complexity_cfg = COMPLEXITY_LEVELS.get(complexity, COMPLEXITY_LEVELS["medium"])

        # SEO level
        seo = blueprint.seo
        if seo.schema_markup and seo.schema_markup.schema_types:
            seo_level = "comprehensive"
        elif seo.open_graph.title or seo.twitter_card.title:
            seo_level = "enhanced"
        else:
            seo_level = "standard"

        # Performance target
        perf_target = str(blueprint.performance.target_lighthouse_score)

        return BlueprintSummary(
            business_type=blueprint.business_category or blueprint.industry or "",
            website_style=blueprint.visual_style or "modern-saas",
            total_sections=section_count,
            total_components=component_count,
            total_assets=asset_count,
            animation_count=animation_count,
            seo_level=seo_level,
            accessibility_level=blueprint.accessibility.wcag_target,
            performance_target=perf_target,
            estimated_pages=complexity_cfg["estimated_pages"],
            estimated_complexity=complexity,
            estimated_ai_tokens=complexity_cfg["estimated_ai_tokens"],
        )

    def export_dict(self, blueprint: WebsiteBlueprint, exclude_meta: bool = True) -> Dict[str, Any]:
        exclude = {"created_at", "builder_status"} if exclude_meta else set()
        return blueprint.model_dump(exclude_none=True, exclude=exclude)

    def export_json(self, blueprint: WebsiteBlueprint, indent: int = 2, exclude_meta: bool = True) -> str:
        return json.dumps(self.export_dict(blueprint, exclude_meta=exclude_meta), indent=indent, default=str)

    def export_yaml(self, blueprint: WebsiteBlueprint, indent: int = 2, exclude_meta: bool = True) -> str:
        try:
            import yaml as _yaml
            data = self.export_dict(blueprint, exclude_meta=exclude_meta)
            return _yaml.dump(data, default_flow_style=False, indent=indent, allow_unicode=True)
        except ImportError:
            data = self.export_dict(blueprint, exclude_meta=exclude_meta)
            return json.dumps(data, indent=indent, default=str)


website_blueprint_builder = WebsiteBlueprintBuilder()
