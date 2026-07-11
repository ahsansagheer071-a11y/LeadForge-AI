import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

from app.services.markdown_engine.constants import (
    CATEGORY_FILENAMES,
    CATEGORY_PRIORITIES,
    GENERATOR_VERSION,
    MARKDOWN_PACKAGE_VERSION,
    MarkdownCategory,
)
from app.services.markdown_engine.content.developer_content import DEVELOPER_MD_CONTENT
from app.services.markdown_engine.content.system_content import SYSTEM_MD_CONTENT
from app.services.markdown_engine.helpers import (
    calculate_word_count,
    estimate_tokens,
    normalize_headings,
    normalize_spacing,
    sanitize_markdown,
    validate_markdown,
)
from app.services.markdown_engine.package_exporter import PackageExporter
from app.services.markdown_engine.schemas import (
    MarkdownDocument,
    MarkdownMetadata,
    MarkdownPackage,
)
from app.services.markdown_engine.asset_manifest import ManifestBuilder
from app.services.markdown_engine.source_content import (
    SourceWebsiteSnapshot,
    format_source_content,
)
from app.services.website_intelligence.schemas import WebsiteProfile


class MarkdownBuilder:
    """Architecture layer for the Markdown Generation Engine.
    Content-building methods are implemented per phase; stubs remain
    for future phases."""

    def __init__(self, blueprint: WebsiteProfile) -> None:
        """Store the blueprint and prepare builder state."""
        self.blueprint = blueprint
        self._documents: Dict[MarkdownCategory, MarkdownDocument] = {}
        self._asset_manifest = None

    def build_system_md(self) -> MarkdownDocument:
        """Build the system.md document — 100% static, client-agnostic identity
        rules. Does NOT read from self.blueprint."""
        content = sanitize_markdown(SYSTEM_MD_CONTENT)
        content = normalize_headings(content)
        content = normalize_spacing(content)
        word_count = calculate_word_count(content)
        estimated_tokens = estimate_tokens(content)
        return MarkdownDocument(
            filename="00-system.md",
            title="AI Identity & System Rules",
            category=MarkdownCategory.SYSTEM.value,
            priority=CATEGORY_PRIORITIES[MarkdownCategory.SYSTEM],
            content=content,
            version=MARKDOWN_PACKAGE_VERSION,
            generated_at=datetime.now(timezone.utc),
            word_count=word_count,
            estimated_tokens=estimated_tokens,
        )

    def build_developer_md(self) -> MarkdownDocument:
        """Build the developer.md document — 100% static engineering standards.
        Does NOT read from self.blueprint."""
        content = sanitize_markdown(DEVELOPER_MD_CONTENT)
        content = normalize_headings(content)
        content = normalize_spacing(content)
        if not validate_markdown(content):
            raise ValueError("developer.md content validation failed — "
                             "missing heading or contains placeholder")
        word_count = calculate_word_count(content)
        estimated_tokens = estimate_tokens(content)
        return MarkdownDocument(
            filename=CATEGORY_FILENAMES[MarkdownCategory.DEVELOPER],
            title="Engineering Standards & Architecture",
            category=MarkdownCategory.DEVELOPER.value,
            priority=CATEGORY_PRIORITIES[MarkdownCategory.DEVELOPER],
            content=content,
            version=MARKDOWN_PACKAGE_VERSION,
            generated_at=datetime.now(timezone.utc),
            word_count=word_count,
            estimated_tokens=estimated_tokens,
        )

    def build_branding_md(self) -> MarkdownDocument:
        """Build the branding.md document — client-specific brand guidelines
        derived from self.blueprint fields. Skips sections with no source data."""
        sections: List[str] = []
        bp = self.blueprint

        # -- Business Overview --
        biz = bp.business
        biz_lines: List[str] = []
        if biz.name:
            biz_lines.append(f"- **Business Name**: {biz.name}")
        if biz.industry:
            biz_lines.append(f"- **Industry**: {biz.industry}")
        if biz.category:
            biz_lines.append(f"- **Business Category**: {biz.category}")
        loc_parts = [p for p in [biz.city, biz.country, biz.address] if p]
        if loc_parts:
            biz_lines.append(f"- **Location**: {', '.join(loc_parts)}")
        if biz_lines:
            sections.append("## Business Overview\n\n" + "\n".join(biz_lines))

        # -- Brand Personality --
        pers = bp.brand.brand_personality
        pers_lines: List[str] = []
        if pers and pers.personality_traits:
            for t in pers.personality_traits:
                pers_lines.append(f"- {t}")
        if pers_lines:
            sections.append("## Brand Personality\n\n" + "\n".join(pers_lines))

        # -- Color System --
        cols = bp.brand.brand_colors
        col_lines: List[str] = []
        for label, attr in [
            ("Primary", "primary"), ("Secondary", "secondary"), ("Accent", "accent"),
            ("Background", "background"), ("Text", "text"), ("Surface", "surface"),
            ("Heading", "heading"), ("Border", "border"), ("Muted", "muted"),
            ("Dark", "dark"), ("Light", "light"),
            ("Success", "success"), ("Warning", "warning"), ("Danger", "danger"),
            ("Info", "info"),
        ]:
            val = getattr(cols, attr, None)
            if val:
                col_lines.append(f"- **{label}**: `{val}`")
        if cols.accessibility_score is not None:
            col_lines.append(f"- **Accessibility Score**: {cols.accessibility_score}")
        if cols.wcag_compliance:
            for key, level in cols.wcag_compliance.items():
                col_lines.append(f"- **{key}**: {level}")
        if col_lines:
            sections.append("## Color System\n\n" + "\n".join(col_lines))

        # -- Typography --
        typo = bp.brand.typography_info
        typo_lines: List[str] = []
        if typo:
            if typo.primary_font:
                typo_lines.append(f"- **Primary Font**: {typo.primary_font}")
            if typo.heading_font:
                typo_lines.append(f"- **Heading Font**: {typo.heading_font}")
            if typo.secondary_font:
                typo_lines.append(f"- **Secondary Font**: {typo.secondary_font}")
            if typo.weights_used:
                typo_lines.append(f"- **Weights Used**: {', '.join(str(w) for w in typo.weights_used)}")
            if typo.hierarchy:
                typo_lines.append("- **Hierarchy**:")
                for level, entry in sorted(typo.hierarchy.items()):
                    parts = []
                    if entry.font_size:
                        parts.append(f"size {entry.font_size}")
                    if entry.line_height:
                        parts.append(f"lh {entry.line_height}")
                    if entry.letter_spacing:
                        parts.append(f"ls {entry.letter_spacing}")
                    if entry.font_weight:
                        parts.append(f"w{entry.font_weight}")
                    if entry.font_family:
                        parts.append(f"font {entry.font_family}")
                    if parts:
                        typo_lines.append(f"  - **{level.upper()}**: {', '.join(parts)}")
        if typo_lines:
            sections.append("## Typography\n\n" + "\n".join(typo_lines))

        # -- Visual Style --
        dl = bp.brand.design_language
        dl_lines: List[str] = []
        if dl and dl.design_language and dl.design_language != "Unclassified":
            dl_lines.append(f"- **Design Language**: {dl.design_language}")
            if dl.confidence_score > 0:
                dl_lines.append(f"- **Confidence**: {dl.confidence_score:.0%}")
            if dl.all_scores:
                for style, score in sorted(dl.all_scores.items(), key=lambda x: -x[1]):
                    dl_lines.append(f"  - {style}: {score:.0%}")
        if dl_lines:
            sections.append("## Visual Style\n\n" + "\n".join(dl_lines))

        # -- Buttons --
        cs = bp.brand.component_styles
        btn_lines: List[str] = []
        if cs and cs.component_styles:
            btn = cs.component_styles.get("button", {})
            if btn:
                for k, v in btn.items():
                    btn_lines.append(f"- **{k.replace('_', ' ').title()}**: {v}")
        if btn_lines:
            sections.append("## Buttons\n\n" + "\n".join(btn_lines))

        # -- Cards --
        card_lines: List[str] = []
        if cs and cs.component_styles:
            card = cs.component_styles.get("card", {})
            if card:
                for k, v in card.items():
                    card_lines.append(f"- **{k.replace('_', ' ').title()}**: {v}")
        if card_lines:
            sections.append("## Cards\n\n" + "\n".join(card_lines))

        # -- Layout Preferences --
        cr = bp.brand.consistency_report
        layout_lines: List[str] = []
        if cr and cr.spacing_consistency is not None:
            layout_lines.append(f"- **Spacing Consistency**: {cr.spacing_consistency:.0%}")
        if layout_lines:
            sections.append("## Layout Preferences\n\n" + "\n".join(layout_lines))

        # -- Accessibility Preferences --
        a11y_lines: List[str] = []
        if cols and cols.accessibility_score is not None:
            a11y_lines.append(f"- **Contrast Level**: {cols.accessibility_score}/10")
        if a11y_lines:
            sections.append("## Accessibility Preferences\n\n" + "\n".join(a11y_lines))

        # -- Brand Rules --
        rules = self._generate_brand_rules()
        if rules:
            sections.append("## Brand Rules\n\n" + "\n".join(rules))

        if not sections:
            raise ValueError("branding.md: no sections could be generated — "
                             "all source fields are empty or None")

        content = "# Branding Guidelines\n\n" + "\n\n".join(sections)
        content = sanitize_markdown(content)
        content = normalize_headings(content)
        content = normalize_spacing(content)

        if not validate_markdown(content):
            raise ValueError("branding.md content validation failed — "
                             "missing heading or contains placeholder")

        wc = calculate_word_count(content)
        et = estimate_tokens(content)
        return MarkdownDocument(
            filename=CATEGORY_FILENAMES[MarkdownCategory.BRANDING],
            title="Brand Identity & Guidelines",
            category=MarkdownCategory.BRANDING.value,
            priority=CATEGORY_PRIORITIES[MarkdownCategory.BRANDING],
            content=content,
            version=MARKDOWN_PACKAGE_VERSION,
            generated_at=datetime.now(timezone.utc),
            word_count=wc,
            estimated_tokens=et,
        )

    def build_layout_md(self) -> MarkdownDocument:
        """Build the layout.md document — client-specific layout structure
        derived from self.blueprint fields."""
        sections: List[str] = []
        bp = self.blueprint
        wl = bp.website_layout

        if wl is None:
            content = "# Website Layout\n\nLayout data is unavailable for this lead."
            content = sanitize_markdown(content)
            content = normalize_spacing(content)
            wc = calculate_word_count(content)
            et = estimate_tokens(content)
            return MarkdownDocument(
                filename=CATEGORY_FILENAMES[MarkdownCategory.LAYOUT],
                title="Website Layout & Structure",
                category=MarkdownCategory.LAYOUT.value,
                priority=CATEGORY_PRIORITIES[MarkdownCategory.LAYOUT],
                content=content,
                version=MARKDOWN_PACKAGE_VERSION,
                generated_at=datetime.now(timezone.utc),
                word_count=wc,
                estimated_tokens=et,
            )

        # -- Page Flow --
        flow_items: List[str] = ["Navigation"]
        for sec in wl.sections:
            flow_items.append(sec.section_type)
        flow_items.append("Footer")
        sections.append("## Page Flow\n\n" + " → ".join(flow_items))

        # -- Section Breakdown --
        breakdown_parts: List[str] = []
        for sec in wl.sections:
            sec_lines: List[str] = []
            sec_lines.append(f"### {sec.section_type}")
            sec_lines.append("")
            sec_lines.append(f"- **Display Order**: {sec.order}")
            if sec.heading:
                sec_lines.append(f"- **Heading**: {sec.heading}")
            if sec.subheading:
                sec_lines.append(f"- **Subheading**: {sec.subheading}")
            if sec.description:
                sec_lines.append(f"- **Description**: {sec.description}")
            sec_lines.append(f"- **Layout Type**: {sec.layout_type}")
            sec_lines.append(f"- **Image Present**: {'Yes' if len(sec.images) > 0 else 'No'}")
            sec_lines.append(f"- **CTA Present**: {'Yes' if len(sec.buttons) > 0 else 'No'}")
            if sec.confidence_score < 100:
                sec_lines.append(f"- **Classification Confidence**: {sec.confidence_score:.0f}%")
            breakdown_parts.append("\n".join(sec_lines))
        if breakdown_parts:
            sections.append("## Section Breakdown\n\n" + "\n\n".join(breakdown_parts))

        # -- Navigation Layout --
        nav = bp.navigation_info
        nav_lines: List[str] = []
        if nav:
            nav_lines.append(f"- **Sticky**: {'Yes' if nav.is_sticky else 'No'}")
            nav_lines.append(f"- **Primary Nav Items**: {len(nav.primary_nav_items)}")
            nav_lines.append(f"- **Secondary Nav Items**: {len(nav.secondary_nav_items)}")
            nav_lines.append(f"- **Footer Nav Items**: {len(nav.footer_nav_items)}")

            dropdowns = [item.label for item in nav.primary_nav_items if item.has_dropdown]
            if dropdowns:
                nav_lines.append(f"- **Dropdowns**: {', '.join(dropdowns)}")
            megamenus = [item.label for item in nav.primary_nav_items if item.is_mega_menu]
            if megamenus:
                nav_lines.append(f"- **Mega Menus**: {', '.join(megamenus)}")
        if nav_lines:
            sections.append("## Navigation Layout\n\n" + "\n".join(nav_lines))

        # -- Hero Layout --
        hero = bp.hero_info
        hero_lines: List[str] = []
        if hero:
            if hero.hero_layout:
                hero_lines.append(f"- **Layout**: {hero.hero_layout}")
            if hero.hero_alignment:
                hero_lines.append(f"- **Alignment**: {hero.hero_alignment}")
            if hero.primary_cta:
                hero_lines.append(f"- **Primary CTA**: {hero.primary_cta.text}")
            if hero.secondary_cta:
                hero_lines.append(f"- **Secondary CTA**: {hero.secondary_cta.text}")
        if hero_lines:
            sections.append("## Hero Layout\n\n" + "\n".join(hero_lines))

        # -- Footer Layout --
        footer = wl.footer_info
        footer_lines: List[str] = []
        if footer:
            footer_lines.append(f"- **Logo Present**: {'Yes' if footer.footer_logo else 'No'}")
            footer_links_labels = [link.label for link in footer.footer_links if link.label]
            if footer_links_labels:
                footer_lines.append(f"- **Navigation Links**: {', '.join(footer_links_labels)}")
            platforms = [s.platform for s in footer.social_links if s.platform]
            if platforms:
                footer_lines.append(f"- **Social Links**: {', '.join(platforms)}")
            if footer.copyright_text:
                footer_lines.append(f"- **Copyright**: {footer.copyright_text}")
            footer_lines.append(f"- **Newsletter Signup**: {'Yes' if footer.newsletter_signup else 'No'}")
        if footer_lines:
            sections.append("## Footer Layout\n\n" + "\n".join(footer_lines))

        # -- Layout Rules --
        rules = self._generate_layout_rules()
        if rules:
            sections.append("## Layout Rules\n\n" + "\n".join(rules))

        content = "# Website Layout\n\n" + "\n\n".join(sections)
        content = sanitize_markdown(content)
        content = normalize_headings(content)
        content = normalize_spacing(content)

        if not validate_markdown(content):
            raise ValueError("layout.md content validation failed — "
                             "missing heading or contains placeholder")

        wc = calculate_word_count(content)
        et = estimate_tokens(content)
        return MarkdownDocument(
            filename=CATEGORY_FILENAMES[MarkdownCategory.LAYOUT],
            title="Website Layout & Structure",
            category=MarkdownCategory.LAYOUT.value,
            priority=CATEGORY_PRIORITIES[MarkdownCategory.LAYOUT],
            content=content,
            version=MARKDOWN_PACKAGE_VERSION,
            generated_at=datetime.now(timezone.utc),
            word_count=wc,
            estimated_tokens=et,
        )

    def _generate_layout_rules(self) -> List[str]:
        """Generate layout rules derived from the actual extracted data."""
        rules: List[str] = []
        wl = self.blueprint.website_layout
        if wl is None:
            return rules

        if wl.sections:
            order_chain = " → ".join(
                f"{s.section_type} (order {s.order})" for s in wl.sections
            )
            rules.append(f"- Preserve the detected section order: {order_chain}.")
            seen: set = set()
            for s in wl.sections:
                if s.section_type in seen:
                    rules.append(f"- Do not duplicate the `{s.section_type}` section — it appears more than once.")
                seen.add(s.section_type)

        nav = self.blueprint.navigation_info
        if nav:
            if nav.is_sticky:
                rules.append("- Keep navigation fixed/sticky as detected on the original site.")
            if nav.navigation_depth > 0:
                rules.append(f"- Preserve the detected navigation depth of {nav.navigation_depth} levels.")

        return rules

    def build_components_md(self) -> MarkdownDocument:
        """Build the components.md document — aggregated component inventory
        derived from self.blueprint fields. Omits components with no data."""
        bp = self.blueprint
        wl = bp.website_layout

        if wl is None:
            content = "# Website Components\n\nComponent data is unavailable for this lead."
            content = sanitize_markdown(content)
            content = normalize_spacing(content)
            wc = calculate_word_count(content)
            et = estimate_tokens(content)
            return MarkdownDocument(
                filename=CATEGORY_FILENAMES[MarkdownCategory.COMPONENTS],
                title="Website Component Inventory",
                category=MarkdownCategory.COMPONENTS.value,
                priority=CATEGORY_PRIORITIES[MarkdownCategory.COMPONENTS],
                content=content,
                version=MARKDOWN_PACKAGE_VERSION,
                generated_at=datetime.now(timezone.utc),
                word_count=wc,
                estimated_tokens=et,
            )

        sections_list: List[str] = []

        # ---- Aggregate counts ----
        nav = bp.navigation_info
        hero = bp.hero_info
        footer = wl.footer_info
        logo_info = bp.brand.logo_info

        total_sections = len(wl.sections)
        total_nav_items = (
            (len(nav.primary_nav_items) if nav else 0) +
            (len(nav.secondary_nav_items) if nav else 0) +
            (len(nav.footer_nav_items) if nav else 0)
        )
        total_ctas = len(wl.ctas) + (
            1 if hero and hero.primary_cta else 0
        ) + (
            1 if hero and hero.secondary_cta else 0
        )
        total_section_images = sum(len(s.images) for s in wl.sections)
        total_section_buttons = sum(len(s.buttons) for s in wl.sections)
        total_buttons = total_section_buttons + total_ctas
        total_images = total_section_images + (
            1 if hero and hero.hero_image else 0
        ) + (
            1 if footer and footer.footer_logo else 0
        ) + (
            1 if logo_info and logo_info.logo_url else 0
        )
        grid_sections = sum(1 for s in wl.sections if s.layout_type == "grid")
        has_newsletter = footer and footer.newsletter_signup
        total_forms = 1 if has_newsletter else 0
        interactive = total_buttons + (
            len(nav.primary_nav_items) if nav else 0
        )

        # -- Component Summary --
        summary_lines: List[str] = []
        summary_lines.append(f"- **Total Sections**: {total_sections}")
        total_components = total_sections + total_nav_items + total_ctas + total_images + total_buttons + total_forms
        summary_lines.append(f"- **Total Components**: {total_components}")
        summary_lines.append(f"- **Buttons**: {total_buttons}")
        summary_lines.append(f"- **Forms**: {total_forms}")
        summary_lines.append(f"- **Cards**: {grid_sections}")
        summary_lines.append(f"- **Images**: {total_images}")
        summary_lines.append(f"- **Navigation Elements**: {total_nav_items}")
        summary_lines.append(f"- **Interactive Elements**: {interactive}")
        sections_list.append("## Component Summary\n\n" + "\n".join(summary_lines))

        # -- Navigation Components --
        nav_lines: List[str] = []
        if nav:
            nav_lines.append(f"- **Navigation Items**: {total_nav_items}")
            dropdowns = [i.label for i in nav.primary_nav_items if i.has_dropdown]
            if dropdowns:
                nav_lines.append(f"- **Dropdowns**: {', '.join(dropdowns)}")
            megamenus = [i.label for i in nav.primary_nav_items if i.is_mega_menu]
            if megamenus:
                nav_lines.append(f"- **Mega Menus**: {', '.join(megamenus)}")
            if logo_info and logo_info.logo_url:
                nav_lines.append("- **Logo**: Present")
            if nav.is_sticky:
                nav_lines.append("- **Sticky**: Yes")
        if nav_lines:
            sections_list.append("## Navigation Components\n\n" + "\n".join(nav_lines))

        # -- Hero Components --
        hero_lines: List[str] = []
        if hero:
            if hero.hero_title:
                hero_lines.append(f"- **Headline**: {hero.hero_title}")
            if hero.hero_subtitle:
                hero_lines.append(f"- **Subheadline**: {hero.hero_subtitle}")
            if hero.primary_cta:
                hero_lines.append(f"- **Primary CTA**: {hero.primary_cta.text}")
            if hero.secondary_cta:
                hero_lines.append(f"- **Secondary CTA**: {hero.secondary_cta.text}")
            if hero.hero_image:
                hero_lines.append("- **Hero Image**: Present")
            if hero.background_image_url:
                hero_lines.append("- **Hero Background**: Present")
        if hero_lines:
            sections_list.append("## Hero Components\n\n" + "\n".join(hero_lines))

        # -- Service / Card / Testimonial / FAQ / Other sections --
        service_sections = [s for s in wl.sections if s.section_type.lower() in ("services", "service")]
        card_sections = [s for s in wl.sections if s.layout_type == "grid"]
        testimonial_sections = [s for s in wl.sections if s.section_type.lower() in ("testimonials", "testimonial")]
        faq_sections = [s for s in wl.sections if s.section_type.lower() in ("faq", "faqs")]

        # -- Service Components --
        svc_lines: List[str] = []
        for s in service_sections:
            if s.heading:
                svc_lines.append(f"- **Heading**: {s.heading}")
            if s.description:
                svc_lines.append(f"- **Description**: {s.description}")
            svc_lines.append(f"- **Buttons**: {len(s.buttons)}")
            svc_lines.append(f"- **Images**: {len(s.images)}")
        if svc_lines:
            sections_list.append("## Service Components\n\n" + "\n".join(svc_lines))

        # -- Card Components --
        card_lines: List[str] = []
        for s in card_sections:
            card_lines.append(f"- **Section**: {s.section_type}")
            card_lines.append(f"  - **Layout Type**: {s.layout_type}")
            card_lines.append(f"  - **Images**: {len(s.images)}")
            card_lines.append(f"  - **Buttons**: {len(s.buttons)}")
        if card_lines:
            sections_list.append("## Card Components\n\n" + "\n".join(card_lines))

        # -- Form Components --
        form_lines: List[str] = []
        if has_newsletter:
            form_lines.append("- **Newsletter**: Present")
            if footer and footer.newsletter_action_url:
                form_lines.append(f"  - **Action URL**: {footer.newsletter_action_url}")
        if form_lines:
            sections_list.append("## Form Components\n\n" + "\n".join(form_lines))

        # -- CTA Components --
        cta_lines: List[str] = []
        for cta in wl.ctas:
            cta_lines.append(f"- **Text**: {cta.text}")
            if cta.position:
                cta_lines.append(f"  - **Position**: {cta.position}")
            if cta.section:
                cta_lines.append(f"  - **Section**: {cta.section}")
            if cta.is_primary:
                cta_lines.append("  - **Type**: Primary")
        if hero and hero.primary_cta:
            cta_lines.append(f"- **Text**: {hero.primary_cta.text}")
            cta_lines.append("  - **Position**: hero")
            cta_lines.append("  - **Type**: Primary")
        if hero and hero.secondary_cta:
            cta_lines.append(f"- **Text**: {hero.secondary_cta.text}")
            cta_lines.append("  - **Position**: hero")
            cta_lines.append("  - **Type**: Secondary")
        if cta_lines:
            sections_list.append("## CTA Components\n\n" + "\n".join(cta_lines))

        # -- Image Components --
        img_lines: List[str] = []
        hero_image_count = 1 if (hero and hero.hero_image) else 0
        section_image_count = total_section_images
        logo_count = (
            (1 if footer and footer.footer_logo else 0) +
            (1 if logo_info and logo_info.logo_url else 0)
        )
        if total_images > 0:
            img_lines.append(f"- **Total Images**: {total_images}")
        if hero_image_count > 0:
            img_lines.append(f"- **Hero Images**: {hero_image_count}")
        if section_image_count > 0:
            img_lines.append(f"- **Section Images**: {section_image_count}")
        if logo_count > 0:
            img_lines.append(f"- **Logos**: {logo_count}")
        if img_lines:
            sections_list.append("## Image Components\n\n" + "\n".join(img_lines))

        # -- Testimonial Components --
        test_lines: List[str] = []
        for s in testimonial_sections:
            test_lines.append("- **Cards**: 1")
            if s.heading:
                test_lines.append(f"- **Heading**: {s.heading}")
            if s.description:
                test_lines.append(f"- **Description**: {s.description}")
            test_lines.append(f"- **Images**: {len(s.images)}")
            if len(s.buttons) > 0:
                test_lines.append(f"- **Buttons**: {len(s.buttons)}")
        if test_lines:
            sections_list.append("## Testimonial Components\n\n" + "\n".join(test_lines))

        # -- FAQ Components --
        faq_lines: List[str] = []
        for s in faq_sections:
            if s.heading:
                faq_lines.append(f"- **Heading**: {s.heading}")
            if s.description:
                faq_lines.append(f"  - **Description**: {s.description}")
            faq_lines.append(f"  - **Layout Type**: {s.layout_type}")
        if faq_lines:
            sections_list.append("## FAQ Components\n\n" + "\n".join(faq_lines))

        # -- Footer Components --
        footer_lines: List[str] = []
        if footer:
            if footer.footer_logo:
                footer_lines.append("- **Logo**: Present")
            if footer.footer_links:
                footer_lines.append(f"- **Navigation**: {len(footer.footer_links)} links")
            platforms = [s.platform for s in footer.social_links if s.platform]
            if platforms:
                footer_lines.append(f"- **Social Links**: {', '.join(platforms)}")
            if footer.newsletter_signup:
                footer_lines.append("- **Newsletter**: Present")
            if footer.copyright_text:
                footer_lines.append(f"- **Copyright**: {footer.copyright_text}")
        if footer_lines:
            sections_list.append("## Footer Components\n\n" + "\n".join(footer_lines))

        # -- Component Rules --
        rules = self._generate_component_rules()
        if rules:
            sections_list.append("## Component Rules\n\n" + "\n".join(rules))

        content = "# Website Components\n\n" + "\n\n".join(sections_list)
        content = sanitize_markdown(content)
        content = normalize_headings(content)
        content = normalize_spacing(content)

        if not validate_markdown(content):
            raise ValueError("components.md content validation failed — "
                             "missing heading or contains placeholder")

        wc = calculate_word_count(content)
        et = estimate_tokens(content)
        return MarkdownDocument(
            filename=CATEGORY_FILENAMES[MarkdownCategory.COMPONENTS],
            title="Website Component Inventory",
            category=MarkdownCategory.COMPONENTS.value,
            priority=CATEGORY_PRIORITIES[MarkdownCategory.COMPONENTS],
            content=content,
            version=MARKDOWN_PACKAGE_VERSION,
            generated_at=now,
            word_count=wc,
            estimated_tokens=et,
        )

    def _generate_component_rules(self) -> List[str]:
        """Generate deterministic component rules from extracted data."""
        rules: List[str] = []
        bp = self.blueprint
        wl = bp.website_layout
        if wl is None:
            return rules

        nav = bp.navigation_info
        hero = bp.hero_info

        if hero and hero.primary_cta and hero.secondary_cta:
            rules.append("- Do not duplicate hero buttons — keep primary and secondary distinct.")
        if nav and nav.primary_nav_items:
            labels = [i.label for i in nav.primary_nav_items]
            rules.append(f"- Keep navigation labels consistent: {', '.join(labels)}.")
        if wl.ctas:
            cta_texts = [c.text for c in wl.ctas if c.text]
            if cta_texts:
                rules.append(f"- Preserve detected CTA wording: {', '.join(cta_texts)}.")
        if wl.sections:
            seen: set = set()
            for s in wl.sections:
                if s.section_type in seen:
                    rules.append(f"- Maintain consistent layout for `{s.section_type}` sections — they appear more than once.")
                seen.add(s.section_type)
        if hero and hero.hero_layout:
            rules.append(f"- Preserve the detected hero layout: `{hero.hero_layout}`.")

        return rules

    def build_seo_md(self) -> MarkdownDocument:
        """Build the seo.md document — SEO metadata derived from
        self.blueprint.seo fields. Omits sections with no backing data."""
        seo = self.blueprint.seo
        sections_list: List[str] = []

        # -- Page Metadata --
        meta_lines: List[str] = []
        if seo.page_title:
            meta_lines.append(f"- **Page Title**: {seo.page_title}")
        if seo.meta_description:
            meta_lines.append(f"- **Meta Description**: {seo.meta_description}")
        if meta_lines:
            sections_list.append("## Page Metadata\n\n" + "\n".join(meta_lines))

        # -- Focus Keywords (extra field found — not in spec's map) --
        kw_lines: List[str] = []
        if seo.focus_keywords:
            kw_lines.append(f"- **Keywords**: {', '.join(seo.focus_keywords)}")
        if kw_lines:
            sections_list.append("## Focus Keywords\n\n" + "\n".join(kw_lines))

        # -- SEO Health Flags --
        flags_lines: List[str] = []
        if seo.missing_title is not None:
            flags_lines.append(f"- **Missing page title**: {'Yes' if seo.missing_title else 'No'}")
        if seo.missing_meta_description is not None:
            flags_lines.append(f"- **Missing meta description**: {'Yes' if seo.missing_meta_description else 'No'}")
        if seo.missing_h1 is not None:
            flags_lines.append(f"- **Missing H1 tag**: {'Yes' if seo.missing_h1 else 'No'}")
        if seo.https_enabled is not None:
            flags_lines.append(f"- **HTTPS enabled**: {'Yes' if seo.https_enabled else 'No'}")
        if seo.ssl_status is not None:
            flags_lines.append(f"- **SSL status**: {'Valid' if seo.ssl_status else 'Invalid/Missing'}")
        if flags_lines:
            sections_list.append("## SEO Health Flags\n\n" + "\n".join(flags_lines))

        # -- Structured Data (does not exist in schema) —
        #    section skipped entirely

        # -- Open Graph (does not exist in schema) —
        #    section skipped entirely

        # -- Twitter Card (does not exist in schema) —
        #    section skipped entirely

        # -- SEO Rules --
        rules = self._generate_seo_rules()
        if rules:
            sections_list.append("## SEO Rules\n\n" + "\n".join(rules))

        if not sections_list:
            content = "# SEO Metadata\n\nSEO metadata was not available for this extraction."
            content = sanitize_markdown(content)
            content = normalize_spacing(content)
            wc = calculate_word_count(content)
            et = estimate_tokens(content)
            return MarkdownDocument(
                filename=CATEGORY_FILENAMES[MarkdownCategory.SEO],
                title="SEO Metadata",
                category=MarkdownCategory.SEO.value,
                priority=CATEGORY_PRIORITIES[MarkdownCategory.SEO],
                content=content,
                version=MARKDOWN_PACKAGE_VERSION,
                generated_at=datetime.now(timezone.utc),
                word_count=wc,
                estimated_tokens=et,
            )

        content = "# SEO Metadata\n\n" + "\n\n".join(sections_list)
        content = sanitize_markdown(content)
        content = normalize_headings(content)
        content = normalize_spacing(content)

        if not validate_markdown(content):
            raise ValueError("seo.md content validation failed — "
                             "missing heading or contains placeholder")

        wc = calculate_word_count(content)
        et = estimate_tokens(content)
        return MarkdownDocument(
            filename=CATEGORY_FILENAMES[MarkdownCategory.SEO],
            title="SEO Metadata",
            category=MarkdownCategory.SEO.value,
            priority=CATEGORY_PRIORITIES[MarkdownCategory.SEO],
            content=content,
            version=MARKDOWN_PACKAGE_VERSION,
            generated_at=datetime.now(timezone.utc),
            word_count=wc,
            estimated_tokens=et,
        )

    def build_animations_md(self) -> MarkdownDocument:
        """Build the animations.md document.

        Inspection across all WebsiteProfile fields found NO per-site
        animation, motion, transition, hover, scroll, or parallax data.
        `self.blueprint.brand.design_language` (DesignLanguageResult —
        visual style classification only), `self.blueprint.brand.consistency_report`
        (ConsistencyReport — consistency scores only), `self.blueprint.website_layout.sections`
        (SectionInfo — no animation fields), and `self.blueprint.hero_info`
        (HeroInfo — no animation fields) all lack animation-specific sub-fields.

        Returns a minimal fallback document pointing to the general guidance
        in developer.md's ## Animations section."""
        bp = self.blueprint

        # -- Check for any per-site animation data --
        animations_data: List[Any] = []
        if bp.blueprint and bp.blueprint.animations_needed:
            animations_data = bp.blueprint.animations_needed

        if not animations_data:
            content = (
                "# Website Animations\n\n"
                "No per-site animation data was captured during extraction. "
                "No animations, transitions, scroll effects, hover effects, "
                "or motion preferences were detected on the original website.\n\n"
                "## Fallback Guidance\n\n"
                "Apply the general animation rules defined in "
                "`developer.md` (`## Animations`):\n\n"
                "- **Library**: Framer Motion only.\n"
                "- **Fade**: Fade in on scroll.\n"
                "- **Slide**: Slide in from bottom or side.\n"
                "- **Scale**: Scale in on scroll.\n"
                "- **Stagger**: Stagger children in lists/grids.\n"
                "- **Scroll Reveal**: Reveal sections on scroll.\n"
                "- **Duration**: 0.25s–0.6s.\n"
                "- **Avoid** excessive motion.\n"
                "- **Respect** `prefers-reduced-motion`."
            )
            content = sanitize_markdown(content)
            content = normalize_headings(content)
            content = normalize_spacing(content)

            wc = calculate_word_count(content)
            et = estimate_tokens(content)
            return MarkdownDocument(
                filename=CATEGORY_FILENAMES[MarkdownCategory.ANIMATIONS],
                title="Animation System",
                category=MarkdownCategory.ANIMATIONS.value,
                priority=CATEGORY_PRIORITIES[MarkdownCategory.ANIMATIONS],
                content=content,
                version=MARKDOWN_PACKAGE_VERSION,
                generated_at=datetime.now(timezone.utc),
                word_count=wc,
                estimated_tokens=et,
            )

        # -- Per-site animation data exists: build full document --
        sections_list: List[str] = []

        summary_lines: List[str] = []
        summary_lines.append(f"- **Total Animations**: {len(animations_data)}")
        types = set()
        for a in animations_data:
            t = a.get("type", a.get("animation_type", "unknown"))
            types.add(t)
        summary_lines.append(f"- **Animation Types**: {', '.join(sorted(types))}")
        sections_list.append("## Animation Summary\n\n" + "\n".join(summary_lines))

        content = "# Website Animations\n\n" + "\n\n".join(sections_list)
        content = sanitize_markdown(content)
        content = normalize_headings(content)
        content = normalize_spacing(content)

        wc = calculate_word_count(content)
        et = estimate_tokens(content)
        return MarkdownDocument(
            filename=CATEGORY_FILENAMES[MarkdownCategory.ANIMATIONS],
            title="Animation System",
            category=MarkdownCategory.ANIMATIONS.value,
            priority=CATEGORY_PRIORITIES[MarkdownCategory.ANIMATIONS],
            content=content,
            version=MARKDOWN_PACKAGE_VERSION,
            generated_at=datetime.now(timezone.utc),
            word_count=wc,
            estimated_tokens=et,
        )

    def build_performance_md(self) -> MarkdownDocument:
        """Build the performance.md document.

        Schema inspection across all WebsiteProfile fields found only
        one genuine performance metric: raw_html_size_kb (raw HTML
        download size). Image counts exist but carry no optimization
        metadata. QualityMetrics all default to Not Analyzed.
        All other performance fields (Lighthouse, load time, script
        counts, font strategies, etc.) are absent.

        Returns either a data-driven document with the detected metric
        or a minimal fallback pointing to developer.md's Performance
        section."""
        bp = self.blueprint

        has_raw_size = bp.raw_html_size_kb is not None

        if not has_raw_size:
            content = (
                "# Performance Metadata\n\n"
                "No performance data was captured during extraction. "
                "No page load time, Lighthouse scores, script counts, "
                "font loading strategies, or any other performance metrics "
                "were detected on the original website."
                "\n\n"
                "## Fallback Guidance\n\n"
                "Apply the general performance rules defined in "
                "`developer.md` (`## Performance`):\n\n"
                "- **Dynamic imports** for code splitting.\n"
                "- **Tree shaking** to eliminate unused code.\n"
                "- **Image optimization** for all assets.\n"
                "- **Minimal bundle size** via code splitting.\n"
                "- **Avoid** unnecessary re-renders."
            )
            content = sanitize_markdown(content)
            content = normalize_headings(content)
            content = normalize_spacing(content)

            if not validate_markdown(content):
                raise ValueError("performance.md content validation failed — "
                                 "missing heading or contains placeholder")

            wc = calculate_word_count(content)
            et = estimate_tokens(content)
            return MarkdownDocument(
                filename=CATEGORY_FILENAMES[MarkdownCategory.PERFORMANCE],
                title="Performance Metadata",
                category=MarkdownCategory.PERFORMANCE.value,
                priority=CATEGORY_PRIORITIES[MarkdownCategory.PERFORMANCE],
                content=content,
                version=MARKDOWN_PACKAGE_VERSION,
                generated_at=datetime.now(timezone.utc),
                word_count=wc,
                estimated_tokens=et,
            )

        # -- Data path: genuine per-site performance data exists --
        sections_list: List[str] = []

        # -- Detected Metrics --
        metric_lines: List[str] = []
        if bp.raw_html_size_kb is not None:
            metric_lines.append(f"- **Raw HTML Size**: {bp.raw_html_size_kb:.1f} KB")
        if metric_lines:
            sections_list.append("## Detected Metrics\n\n" + "\n".join(metric_lines))

        # -- Image Optimization Signals --
        total_images = len(bp.images)
        section_images = 0
        if bp.website_layout:
            section_images = sum(len(s.images) for s in bp.website_layout.sections)
        image_lines: List[str] = []
        if total_images > 0 or section_images > 0:
            image_lines.append(f"- **Total Images Captured**: {total_images}")
            image_lines.append(
                f"- **Section Images Detected**: {section_images} "
                "(raw count — no optimization metadata was captured)"
            )
        if image_lines:
            sections_list.append("## Image Optimization Signals\n\n" + "\n".join(image_lines))

        # -- Performance Rules --
        rules_lines: List[str] = [
            "- Apply general performance rules from `developer.md` (`## Performance`) "
            "as baseline (dynamic imports, code splitting, tree shaking, "
            "image optimization)."
        ]
        if bp.raw_html_size_kb is not None:
            rules_lines.append(
                f"- Preserve the detected raw HTML size ({bp.raw_html_size_kb:.1f} KB) "
                "as a sizing reference."
            )
        if total_images > 0:
            rules_lines.append(
                f"- Optimize all {total_images} extracted images "
                "(WebP/AVIF, lazy loading, responsive sizes)."
            )
        sections_list.append("## Performance Rules\n\n" + "\n".join(rules_lines))

        content = "# Performance Metadata\n\n" + "\n\n".join(sections_list)
        content = sanitize_markdown(content)
        content = normalize_headings(content)
        content = normalize_spacing(content)

        if not validate_markdown(content):
            raise ValueError("performance.md content validation failed — "
                             "missing heading or contains placeholder")

        wc = calculate_word_count(content)
        et = estimate_tokens(content)
        return MarkdownDocument(
            filename=CATEGORY_FILENAMES[MarkdownCategory.PERFORMANCE],
            title="Performance Metadata",
            category=MarkdownCategory.PERFORMANCE.value,
            priority=CATEGORY_PRIORITIES[MarkdownCategory.PERFORMANCE],
            content=content,
            version=MARKDOWN_PACKAGE_VERSION,
            generated_at=datetime.now(timezone.utc),
            word_count=wc,
            estimated_tokens=et,
        )

    def build_accessibility_md(self) -> MarkdownDocument:
        """Build the accessibility.md document — color-contrast accessibility
        data from self.blueprint.brand.brand_colors, alt-text presence from
        self.blueprint.images. No dedicated aria/keyboard/screen-reader
        fields exist on WebsiteProfile — those sections are omitted."""
        bp = self.blueprint
        cols = bp.brand.brand_colors
        sections_list: List[str] = []

        # -- Accessibility Summary --
        a11y_summary: List[str] = []
        if cols.accessibility_score is not None:
            a11y_summary.append(f"- **Overall Score**: {cols.accessibility_score}/100")
            if cols.accessibility_score >= 90:
                a11y_summary.append("- **Rating**: Excellent")
            elif cols.accessibility_score >= 70:
                a11y_summary.append("- **Rating**: Good")
            elif cols.accessibility_score >= 50:
                a11y_summary.append("- **Rating**: Fair")
            else:
                a11y_summary.append("- **Rating**: Poor")
        if cols.wcag_compliance:
            levels = set(cols.wcag_compliance.values())
            for level in sorted(levels):
                count = sum(1 for v in cols.wcag_compliance.values() if v == level)
                a11y_summary.append(f"- **{level}**: {count} pair(s)")
        if a11y_summary:
            sections_list.append("## Accessibility Summary\n\n" + "\n".join(a11y_summary))

        # -- Color Contrast --
        contrast_lines: List[str] = []
        if cols.contrast_ratios and cols.wcag_compliance:
            shared_keys = set(cols.contrast_ratios.keys()) & set(cols.wcag_compliance.keys())
            for key in sorted(shared_keys):
                ratio = cols.contrast_ratios[key]
                level = cols.wcag_compliance[key]
                label = key.replace("_", " ").replace("on ", "on ").title()
                contrast_lines.append(f"- **{label}**: {ratio:.1f}:1 ({level})")
        if contrast_lines:
            sections_list.append("## Color Contrast\n\n" + "\n".join(contrast_lines))

        # -- Poor Combinations --
        if cols.poor_combinations:
            poor_lines: List[str] = []
            for pc in cols.poor_combinations:
                element = pc.element_pair or f"{pc.foreground} on {pc.background}"
                poor_lines.append(
                    f"- **{element}**: {pc.contrast_ratio:.1f}:1 "
                    f"({pc.wcag_compliance})"
                )
            sections_list.append("## Poor Combinations\n\n" + "\n".join(poor_lines))

        # -- Images --
        images = bp.images
        if images:
            img_lines: List[str] = []
            total = len(images)
            with_alt = sum(1 for img in images if img.alt)
            missing_alt = total - with_alt
            img_lines.append(f"- **Total Images**: {total}")
            img_lines.append(f"- **With Alt Text**: {with_alt}")
            if missing_alt > 0:
                img_lines.append(f"- **Missing Alt Text**: {missing_alt}")
            sections_list.append("## Images\n\n" + "\n".join(img_lines))

        # -- No data at all: fallback --
        if not sections_list:
            content = (
                "# Website Accessibility\n\n"
                "No accessibility data was captured during extraction. "
                "No color-contrast scores, WCAG compliance data, "
                "or image alt-text information was detected."
                "\n\n"
                "## Fallback Guidance\n\n"
                "Apply the general accessibility rules defined in "
                "`developer.md` (`## Accessibility`):\n\n"
                "- **Semantic HTML** for all elements.\n"
                "- **Keyboard navigation** for all interactive elements.\n"
                "- **ARIA attributes** where semantic HTML is insufficient.\n"
                "- **Visible focus states** for all interactive elements.\n"
                "- **WCAG AA compliance** as the minimum target."
            )
            content = sanitize_markdown(content)
            content = normalize_headings(content)
            content = normalize_spacing(content)

            if not validate_markdown(content):
                raise ValueError("accessibility.md content validation failed — "
                                 "missing heading or contains placeholder")

            wc = calculate_word_count(content)
            et = estimate_tokens(content)
            return MarkdownDocument(
                filename=CATEGORY_FILENAMES[MarkdownCategory.ACCESSIBILITY],
                title="Website Accessibility",
                category=MarkdownCategory.ACCESSIBILITY.value,
                priority=CATEGORY_PRIORITIES[MarkdownCategory.ACCESSIBILITY],
                content=content,
                version=MARKDOWN_PACKAGE_VERSION,
                generated_at=datetime.now(timezone.utc),
                word_count=wc,
                estimated_tokens=et,
            )

        content = "# Website Accessibility\n\n" + "\n\n".join(sections_list)
        content = sanitize_markdown(content)
        content = normalize_headings(content)
        content = normalize_spacing(content)

        if not validate_markdown(content):
            raise ValueError("accessibility.md content validation failed — "
                             "missing heading or contains placeholder")

        wc = calculate_word_count(content)
        et = estimate_tokens(content)
        return MarkdownDocument(
            filename=CATEGORY_FILENAMES[MarkdownCategory.ACCESSIBILITY],
            title="Website Accessibility",
            category=MarkdownCategory.ACCESSIBILITY.value,
            priority=CATEGORY_PRIORITIES[MarkdownCategory.ACCESSIBILITY],
            content=content,
            version=MARKDOWN_PACKAGE_VERSION,
            generated_at=datetime.now(timezone.utc),
            word_count=wc,
            estimated_tokens=et,
        )

    def build_assets_md(self) -> MarkdownDocument:
        """Build the assets.md document — logo, images, and icons
        extracted from WebsiteProfile. No video or downloadable-file
        fields exist on any sub-schema — those sections are omitted."""
        bp = self.blueprint
        sections_list: List[str] = []

        # -- Gather source data --
        logo = bp.brand.logo_info
        wl = bp.website_layout
        footer = wl.footer_info if wl else None
        hero = bp.hero_info
        cs = bp.brand.component_styles
        image_assets = bp.images

        section_image_count = 0
        section_images_by_section: List[tuple] = []
        if wl:
            for sec in wl.sections:
                if sec.images:
                    section_image_count += len(sec.images)
                    section_images_by_section.append((sec.section_type, sec.images))

        hero_image_url = hero.hero_image if hero else None
        footer_logo_url = footer.footer_logo if footer else None

        total_logo_images = (
            (1 if logo and logo.logo_url else 0) +
            (1 if footer_logo_url else 0)
        )
        total_hero_images = 1 if hero_image_url else 0
        total_section_images = section_image_count
        total_captured_images = len(image_assets)

        has_icon_style = bool(cs and cs.component_styles and "icon" in cs.component_styles)

        # -- Asset Summary --
        summary_lines: List[str] = []
        if logo and logo.logo_url:
            summary_lines.append(f"- **Logo**: Present")
        if footer_logo_url:
            summary_lines.append(f"- **Footer Logo**: Present")
        if hero_image_url:
            summary_lines.append(f"- **Hero Image**: Present")
        if total_section_images > 0:
            summary_lines.append(f"- **Section Images**: {total_section_images}")
        if total_captured_images > 0:
            summary_lines.append(f"- **Captured Image Assets**: {total_captured_images}")
        if has_icon_style:
            icon_count = len(cs.component_styles.get("icon", {}))
            summary_lines.append(f"- **Icons**: {icon_count} style(s)")
        if summary_lines:
            sections_list.append("## Asset Summary\n\n" + "\n".join(summary_lines))

        # -- Logo Assets --
        logo_lines: List[str] = []
        if logo:
            if logo.logo_url:
                logo_lines.append(f"- **URL**: {logo.logo_url}")
            if logo.format:
                logo_lines.append(f"- **Format**: {logo.format}")
            if logo.estimated_width and logo.estimated_height:
                logo_lines.append(f"- **Dimensions**: {logo.estimated_width}x{logo.estimated_height}")
            if logo.dominant_colors:
                logo_lines.append(f"- **Dominant Colors**: {', '.join(logo.dominant_colors)}")
            if logo.position:
                logo_lines.append(f"- **Position**: {logo.position}")
            if logo.has_transparent_background is not None:
                logo_lines.append(f"- **Transparent Background**: {'Yes' if logo.has_transparent_background else 'No'}")
            if logo.is_retina_quality:
                logo_lines.append("- **Retina Quality**: Yes")
        if footer_logo_url:
            logo_lines.append(f"- **Footer Logo URL**: {footer_logo_url}")
        if logo_lines:
            sections_list.append("## Logo Assets\n\n" + "\n".join(logo_lines))

        # -- Images --
        image_sections: List[str] = []

        if hero_image_url:
            image_sections.append(
                "### Hero Image\n\n"
                f"- **URL**: {hero_image_url}"
            )

        for sec_name, urls in section_images_by_section:
            sec_lines: List[str] = [f"### {sec_name}"]
            for url in urls:
                sec_lines.append(f"- **URL**: {url}")
                matched = next((a for a in image_assets if a.url == url), None)
                if matched and matched.alt:
                    sec_lines.append(f"  - **Alt**: {matched.alt}")
            image_sections.append("\n".join(sec_lines))

        if image_sections:
            sections_list.append("## Images\n\n" + "\n\n".join(image_sections))

        # -- Icons --
        icon_lines: List[str] = []
        if has_icon_style:
            icon_data = cs.component_styles["icon"]
            for k, v in icon_data.items():
                icon_lines.append(f"- **{k.replace('_', ' ').title()}**: {v}")
        if icon_lines:
            sections_list.append("## Icons\n\n" + "\n".join(icon_lines))

        # -- Videos: OMITTED entirely (no video field exists on any sub-schema) --
        # -- Downloadable Files: OMITTED entirely (no such field exists) --

        # -- No data at all: fallback --
        if not sections_list:
            content = (
                "# Website Assets\n\n"
                "No asset data was captured during extraction. "
                "No logo, images, or icons were detected on the original website."
                "\n\n"
                "## Fallback Guidance\n\n"
                "Apply the general asset rules defined in "
                "`developer.md` (`## Images` and `## Icons`):\n\n"
                "- **Use Next Image** for all images.\n"
                "- **Lazy loading** for non-hero images.\n"
                "- **Responsive sizes** for all images.\n"
                "- **Priority only for hero** image.\n"
                "- **Lucide Icons** only, consistent stroke width and sizing."
            )
            content = sanitize_markdown(content)
            content = normalize_headings(content)
            content = normalize_spacing(content)

            if not validate_markdown(content):
                raise ValueError("assets.md content validation failed — "
                                 "missing heading or contains placeholder")

            wc = calculate_word_count(content)
            et = estimate_tokens(content)
            return MarkdownDocument(
                filename=CATEGORY_FILENAMES[MarkdownCategory.ASSETS],
                title="Website Assets",
                category=MarkdownCategory.ASSETS.value,
                priority=CATEGORY_PRIORITIES[MarkdownCategory.ASSETS],
                content=content,
                version=MARKDOWN_PACKAGE_VERSION,
                generated_at=datetime.now(timezone.utc),
                word_count=wc,
                estimated_tokens=et,
            )

        # -- Asset Rules --
        rules: List[str] = []
        if logo and logo.logo_url:
            rules.append(f"- Preserve original logo at `{logo.logo_url}`.")
        if logo and logo.format:
            rules.append(f"- Maintain logo format (`{logo.format}`) if a matching "
                         "file format is used in the new site.")
        if hero_image_url:
            rules.append(f"- Keep the hero image as the primary visual asset.")
        if total_section_images > 0:
            rules.append(f"- Optimize {total_section_images} section images "
                         "for the rebuild (responsive, lazy-loaded).")
        if has_icon_style:
            rules.append("- Use Lucide Icons matching the detected icon style "
                         "(outline, solid, etc.).")
        if rules:
            sections_list.append("## Asset Rules\n\n" + "\n".join(rules))

        content = "# Website Assets\n\n" + "\n\n".join(sections_list)
        content = sanitize_markdown(content)
        content = normalize_headings(content)
        content = normalize_spacing(content)

        if not validate_markdown(content):
            raise ValueError("assets.md content validation failed — "
                             "missing heading or contains placeholder")

        wc = calculate_word_count(content)
        et = estimate_tokens(content)
        return MarkdownDocument(
            filename=CATEGORY_FILENAMES[MarkdownCategory.ASSETS],
            title="Website Assets",
            category=MarkdownCategory.ASSETS.value,
            priority=CATEGORY_PRIORITIES[MarkdownCategory.ASSETS],
            content=content,
            version=MARKDOWN_PACKAGE_VERSION,
            generated_at=datetime.now(timezone.utc),
            word_count=wc,
            estimated_tokens=et,
        )

    def build_rules_md(self) -> MarkdownDocument:
        """Build the rules.md document — the MASTER RULEBOOK.

        Every rule traces back to a real field on self.blueprint using
        field paths already verified in Phases 3.4–3.10. Categories with
        no backing data are omitted entirely."""
        bp = self.blueprint
        sections_list: List[str] = []

        # ================================================================
        # General Rules (always included)
        # ================================================================
        general: List[str] = [
            "- Never invent business information.",
            "- Never change extracted content.",
            "- Never remove detected sections.",
        ]

        wl = bp.website_layout
        if wl and wl.sections:
            order_chain = " → ".join(s.section_type for s in wl.sections)
            general.append(f"- Preserve section order: {order_chain}.")
            names = sorted(set(s.section_type for s in wl.sections))
            general.append(f"- Only include sections detected in this WebsiteProfile: "
                           f"{', '.join(names)}.")
        sections_list.append("## General Rules\n\n" + "\n".join(general))

        # ================================================================
        # Branding Rules
        # ================================================================
        brand_rules: List[str] = []
        cols = bp.brand.brand_colors
        typo = bp.brand.typography_info
        logo = bp.brand.logo_info
        dl = bp.brand.design_language
        pers = bp.brand.brand_personality
        cs = bp.brand.component_styles

        if cols:
            if cols.primary:
                brand_rules.append(f"- Preserve primary color: `{cols.primary}`.")
            if cols.secondary:
                brand_rules.append(f"- Preserve secondary color: `{cols.secondary}`.")
            if cols.accent:
                brand_rules.append(f"- Preserve accent color: `{cols.accent}`.")
            if cols.background:
                brand_rules.append(f"- Preserve background color: `{cols.background}`.")
            if cols.text:
                brand_rules.append(f"- Preserve text color: `{cols.text}`.")
        if typo:
            if typo.primary_font:
                brand_rules.append(f"- Use `{typo.primary_font}` for body text.")
            if typo.heading_font:
                brand_rules.append(f"- Use `{typo.heading_font}` for headings.")
            if typo.weights_used:
                weights = sorted(typo.weights_used)
                brand_rules.append(f"- Restrict font weights to {', '.join(str(w) for w in weights)}.")
        if logo:
            if logo.logo_url:
                brand_rules.append(f"- Preserve original logo at `{logo.logo_url}`.")
            if logo.format:
                brand_rules.append(f"- Maintain logo format: `{logo.format}`.")
        if dl and dl.design_language and dl.design_language != "Unclassified":
            brand_rules.append(f"- Follow the detected design language: `{dl.design_language}`.")
        if pers and pers.personality_traits:
            traits = ", ".join(pers.personality_traits)
            brand_rules.append(f"- Reflect brand personality traits: {traits}.")
        if cs and cs.component_styles:
            btn = cs.component_styles.get("button", {})
            if btn:
                for k, v in btn.items():
                    label = k.replace("_", " ").title()
                    brand_rules.append(f"- Use button {label}: `{v}`.")
            card = cs.component_styles.get("card", {})
            if card:
                for k, v in card.items():
                    label = k.replace("_", " ").title()
                    brand_rules.append(f"- Use card {label}: `{v}`.")
        if brand_rules:
            sections_list.append("## Branding Rules\n\n" + "\n".join(brand_rules))

        # ================================================================
        # Layout Rules
        # ================================================================
        layout_rules: List[str] = []
        nav = bp.navigation_info
        hero = bp.hero_info

        if wl and wl.sections:
            order_display = " → ".join(
                f"{s.section_type} (order {s.order})" for s in wl.sections
            )
            layout_rules.append(f"- Follow the detected page flow: {order_display}.")
            for s in wl.sections:
                if s.heading:
                    layout_rules.append(f"- Use heading `{s.heading}` for the `{s.section_type}` section.")
        if nav:
            labels = [i.label for i in nav.primary_nav_items if i.label]
            if labels:
                layout_rules.append(f"- Preserve navigation link order: {', '.join(labels)}.")
            if nav.is_sticky:
                layout_rules.append("- Keep navigation sticky as detected.")
        if hero:
            if hero.hero_layout:
                layout_rules.append(f"- Follow the detected hero layout: `{hero.hero_layout}`.")
            if hero.hero_alignment:
                layout_rules.append(f"- Align hero content: `{hero.hero_alignment}`.")
        if wl and wl.footer_info:
            fi = wl.footer_info
            if fi.footer_links:
                link_labels = [l.label for l in fi.footer_links if l.label]
                if link_labels:
                    layout_rules.append(f"- Preserve footer link order: {', '.join(link_labels)}.")
            platforms = [s.platform for s in fi.social_links if s.platform]
            if platforms:
                layout_rules.append(f"- Include social links: {', '.join(platforms)}.")
        if layout_rules:
            sections_list.append("## Layout Rules\n\n" + "\n".join(layout_rules))

        # ================================================================
        # Component Rules
        # ================================================================
        comp_rules: List[str] = []
        if wl:
            if wl.ctas:
                cta_texts = [c.text for c in wl.ctas if c.text]
                if cta_texts:
                    comp_rules.append(f"- Preserve all detected CTA wording: {', '.join(cta_texts)}.")
            total_sec_images = sum(len(s.images) for s in wl.sections)
            if total_sec_images > 0:
                comp_rules.append(f"- Include all {total_sec_images} section images in the rebuild.")
            total_sec_buttons = sum(len(s.buttons) for s in wl.sections)
            if total_sec_buttons > 0:
                comp_rules.append(f"- Include all {total_sec_buttons} section buttons.")
        if bp.images:
            comp_rules.append(f"- Preserve all {len(bp.images)} captured image assets.")
        if hero:
            if hero.primary_cta:
                comp_rules.append(f"- Keep primary CTA: `{hero.primary_cta.text}`.")
            if hero.secondary_cta:
                comp_rules.append(f"- Keep secondary CTA: `{hero.secondary_cta.text}`.")
        if comp_rules:
            sections_list.append("## Component Rules\n\n" + "\n".join(comp_rules))

        # ================================================================
        # SEO Rules
        # ================================================================
        seo_rules: List[str] = []
        seo = bp.seo
        if seo.page_title:
            seo_rules.append(f"- Preserve page title: `{seo.page_title}`.")
        if seo.meta_description:
            seo_rules.append(f"- Preserve meta description: `{seo.meta_description}`.")
        if seo.focus_keywords:
            seo_rules.append(f"- Target detected keywords: {', '.join(seo.focus_keywords)}.")
        if seo.https_enabled:
            seo_rules.append("- Enforce HTTPS for all pages.")
        if seo.missing_title:
            seo_rules.append("- Ensure every page has a unique `<title>` tag.")
        if seo.missing_meta_description:
            seo_rules.append("- Ensure every page has a unique meta description.")
        if seo.missing_h1:
            seo_rules.append("- Ensure every page has exactly one `<h1>` element.")
        if seo_rules:
            sections_list.append("## SEO Rules\n\n" + "\n".join(seo_rules))

        # ================================================================
        # Accessibility Rules
        # ================================================================
        a11y_rules: List[str] = []
        if cols:
            if cols.contrast_ratios and cols.wcag_compliance:
                shared = set(cols.contrast_ratios.keys()) & set(cols.wcag_compliance.keys())
                for key in sorted(shared):
                    ratio = cols.contrast_ratios[key]
                    level = cols.wcag_compliance[key]
                    label = key.replace("_", " ").title()
                    a11y_rules.append(f"- Maintain {level} contrast ({ratio:.1f}:1) for `{label}`.")
            if cols.poor_combinations:
                a11y_rules.append(
                    f"- Fix {len(cols.poor_combinations)} poor contrast combination(s) "
                    f"that failed WCAG compliance."
                )
            if cols.accessibility_score is not None:
                a11y_rules.append(f"- Target overall accessibility score: {cols.accessibility_score}/100.")
        images = bp.images
        if images:
            missing_alt = sum(1 for img in images if not img.alt)
            if missing_alt > 0:
                a11y_rules.append(f"- Add alt text to {missing_alt} image(s) missing it.")
        if a11y_rules:
            sections_list.append("## Accessibility Rules\n\n" + "\n".join(a11y_rules))

        # ================================================================
        # Asset Rules
        # ================================================================
        asset_rules: List[str] = []
        if logo and logo.logo_url:
            asset_rules.append(f"- Preserve original logo at `{logo.logo_url}`.")
        if wl and wl.footer_info and wl.footer_info.footer_logo:
            asset_rules.append(f"- Preserve footer logo at `{wl.footer_info.footer_logo}`.")
        if hero and hero.hero_image:
            asset_rules.append(f"- Keep hero image as primary visual asset.")
        total_section_images = sum(len(s.images) for s in (wl.sections if wl else []))
        if total_section_images > 0:
            asset_rules.append(f"- Optimize {total_section_images} section images for the rebuild.")
        cs_icon = cs and cs.component_styles and "icon" in cs.component_styles
        if cs_icon:
            icon_style = cs.component_styles["icon"]
            parts = [f"{k}: {v}" for k, v in icon_style.items()]
            if parts:
                asset_rules.append(f"- Use detected icon style: {', '.join(parts)}.")
        if asset_rules:
            sections_list.append("## Asset Rules\n\n" + "\n".join(asset_rules))

        # ================================================================
        # Animation Rules — OMIT unless blueprint.blueprint.animations_needed
        # is genuinely populated (expected empty)
        # ================================================================
        anim_data = bp.blueprint and bp.blueprint.animations_needed
        if anim_data:
            anim_rules: List[str] = []
            for a in anim_data:
                atype = a.get("type", a.get("animation_type", "unknown"))
                target = a.get("target", a.get("target_component", "unknown"))
                anim_rules.append(f"- Apply `{atype}` animation to `{target}`.")
            if anim_rules:
                sections_list.append("## Animation Rules\n\n" + "\n".join(anim_rules))

        # ================================================================
        # Performance Rules — OMIT unless raw_html_size_kb is populated
        # or QualityMetrics has real (non-default) values
        # ================================================================
        perf_rules: List[str] = []
        if bp.raw_html_size_kb is not None:
            perf_rules.append(f"- Reference the detected raw HTML size "
                              f"({bp.raw_html_size_kb:.1f} KB) as a sizing baseline.")
        qm = bp.quality_metrics
        if qm:
            perf_fields = {
                "mobile_readiness": "Mobile Readiness",
                "seo_readiness": "SEO Readiness",
            }
            for field, label in perf_fields.items():
                metric = getattr(qm, field, None)
                if metric and metric.status not in ("Not Analyzed",):
                    perf_rules.append(f"- Target {label} score: {metric.score} ({metric.grade}).")
        if perf_rules:
            sections_list.append("## Performance Rules\n\n" + "\n".join(perf_rules))

        # ================================================================
        # Redesign Rules (always included)
        # ================================================================
        redesign_rules: List[str] = [
            "- REDESIGN the supplied source website ONLY.",
            "- Use the supplied text VERBATIM — do not paraphrase, rewrite, or improve business claims.",
            "- Use ONLY approved source images from the Asset Manifest.",
            "- Do NOT create missing information or sections not present in the source.",
            "- Do NOT use Lorem Ipsum placeholder text.",
            "- Do NOT create \"Service 1\", \"Service 2\", or similar dummy entries.",
            "- Do NOT add LeadForge branding, logos, or watermarks.",
            "- Do NOT add fake testimonials or reviews.",
            "- Do NOT add fake contact details (email, phone, address).",
            "- Do NOT omit any meaningful source section.",
            "- Produce a complete, responsive, single-file HTML document.",
            "- Every <img> src must point to an approved asset from the Asset Manifest.",
            "- Never use stock photos, AI-generated images, or unsplash placeholders.",
        ]
        sections_list.append("## Redesign Rules\n\n" + "\n".join(redesign_rules))

        # ================================================================
        # Global Constraints (always included)
        # ================================================================
        global_rules: List[str] = [
            "- Never hallucinate missing content.",
            "- Never create fake services.",
            "- Never modify customer information.",
            "- Never rewrite testimonials.",
            "- Never invent contact information.",
            "- Never change extracted URLs.",
            "- Never generate unsupported sections.",
        ]
        sections_list.append("## Global Constraints\n\n" + "\n".join(global_rules))

        # ================================================================
        # Assemble document
        # ================================================================
        content = "# Website Generation Rules\n\n" + "\n\n".join(sections_list)
        content = sanitize_markdown(content)
        content = normalize_headings(content)
        content = normalize_spacing(content)

        if not validate_markdown(content):
            raise ValueError("rules.md content validation failed — "
                             "missing heading or contains placeholder")

        wc = calculate_word_count(content)
        et = estimate_tokens(content)
        return MarkdownDocument(
            filename=CATEGORY_FILENAMES[MarkdownCategory.RULES],
            title="Website Generation Rules",
            category=MarkdownCategory.RULES.value,
            priority=CATEGORY_PRIORITIES[MarkdownCategory.RULES],
            content=content,
            version=MARKDOWN_PACKAGE_VERSION,
            generated_at=datetime.now(timezone.utc),
            word_count=wc,
            estimated_tokens=et,
        )

    def build_output_md(self,
                        generated_documents: Dict[str, MarkdownDocument]) -> MarkdownDocument:
        """Build the output.md document — the FINAL ORCHESTRATION MANIFEST.

        Inspects only document metadata (filename, category) from the
        generated_documents dict to determine what exists. Never reads
        .content of any other document."""
        # Fixed reference order for all 11 categories
        fixed_order = [
            ("system", MarkdownCategory.SYSTEM),
            ("developer", MarkdownCategory.DEVELOPER),
            ("branding", MarkdownCategory.BRANDING),
            ("layout", MarkdownCategory.LAYOUT),
            ("components", MarkdownCategory.COMPONENTS),
            ("animations", MarkdownCategory.ANIMATIONS),
            ("seo", MarkdownCategory.SEO),
            ("performance", MarkdownCategory.PERFORMANCE),
            ("accessibility", MarkdownCategory.ACCESSIBILITY),
            ("assets", MarkdownCategory.ASSETS),
            ("rules", MarkdownCategory.RULES),
        ]

        # Determine which documents are present
        present: List[tuple] = []
        for key, cat in fixed_order:
            if key in generated_documents:
                doc = generated_documents[key]
                present.append((key, doc.filename, cat))

        sections_list: List[str] = []

        # -- Package Summary --
        summary_lines: List[str] = []
        for key, filename, cat in present:
            summary_lines.append(f"- {filename}")
        if summary_lines:
            sections_list.append(
                "## Package Summary\n\n" + "\n".join(summary_lines)
            )

        # -- Generation Order --
        order_lines: List[str] = []
        for i, (key, filename, cat) in enumerate(present, 1):
            order_lines.append(f"- {i}. {filename}")
        if order_lines:
            sections_list.append(
                "## Generation Order\n\n" + "\n".join(order_lines)
            )

        # -- Priority Rules --
        priority_lines: List[str] = []
        if present:
            priority_lines.append(
                "- Documents must be consumed in the order listed above "
                "(Generation Order)"
            )
            priority_lines.append(
                "- Earlier documents in the order take precedence "
                "over later ones in case of conflicting guidance"
            )
        if priority_lines:
            sections_list.append(
                "## Priority Rules\n\n" + "\n".join(priority_lines)
            )

        # -- Conflict Resolution --
        conflict_lines: List[str] = []
        cat_names = [key for key, _, _ in present]

        if "branding" in cat_names and "components" in cat_names:
            conflict_lines.append(
                "- If branding conflicts with components, "
                "branding wins (higher priority)"
            )
        if "layout" in cat_names and "components" in cat_names:
            conflict_lines.append(
                "- If layout conflicts with components, "
                "layout wins (higher priority)"
            )
        if "rules" in cat_names:
            conflict_lines.append(
                "- If rules.md defines a restriction, "
                "rules.md overrides implementation decisions "
                "from any other document"
            )
        if conflict_lines:
            sections_list.append(
                "## Conflict Resolution\n\n" + "\n".join(conflict_lines)
            )

        # -- Generation Workflow --
        workflow_steps: List[str] = [
            "- Read the full package and confirm all expected documents are present"
        ]
        if "branding" in cat_names:
            workflow_steps.append("- Load branding identity (branding.md)")
        if "layout" in cat_names:
            workflow_steps.append("- Load layout structure (layout.md)")
        if "components" in cat_names:
            workflow_steps.append("- Load component inventory (components.md)")
        if "system" in cat_names:
            workflow_steps.append("- Apply AI system rules (system.md)")
        if "developer" in cat_names:
            workflow_steps.append("- Apply engineering standards (developer.md)")
        if "seo" in cat_names:
            workflow_steps.append("- Apply SEO configuration (seo.md)")
        if "animations" in cat_names:
            workflow_steps.append("- Apply animation system (animations.md)")
        if "performance" in cat_names:
            workflow_steps.append("- Apply performance targets (performance.md)")
        if "accessibility" in cat_names:
            workflow_steps.append("- Apply accessibility requirements (accessibility.md)")
        if "assets" in cat_names:
            workflow_steps.append("- Apply asset specifications (assets.md)")
        if "rules" in cat_names:
            workflow_steps.append("- Apply coding standards and generation rules (rules.md)")
        workflow_steps.append("- Generate the final website following all document guidance")

        sections_list.append(
            "## Generation Workflow\n\n" + "\n".join(workflow_steps)
        )

        # -- Validation Checklist --
        checklist_lines: List[str] = []
        checks = {
            "system": "AI system rules loaded",
            "developer": "Engineering standards loaded",
            "branding": "Business/brand information loaded",
            "layout": "Layout structure loaded",
            "components": "Component inventory loaded",
            "animations": "Animation system loaded",
            "seo": "SEO configuration loaded",
            "performance": "Performance targets loaded",
            "accessibility": "Accessibility requirements loaded",
            "assets": "Asset specifications loaded",
            "rules": "Generation rules loaded",
        }
        for key, filename, cat in present:
            label = checks.get(key, f"{filename} loaded")
            checklist_lines.append(f"- [ ] {label} ({filename})")
        if checklist_lines:
            sections_list.append(
                "## Validation Checklist\n\n" + "\n".join(checklist_lines)
            )

        # -- Output Format Specification --
        format_lines: List[str] = [
            "You must respond with a structured list of project files.",
            "Your response MUST follow this exact format:",
            "",
            "project_name: <project_name>",
            "",
            "## Files",
            "",
            "app/layout.tsx - Root layout",
            "app/page.tsx - Home page",
            "app/about/page.tsx - About page",
            "components/sections/HeroSection.tsx",
            "components/sections/ServicesSection.tsx",
            "components/sections/FooterSection.tsx",
            "styles/globals.css",
            "lib/utils.ts",
            "tailwind.config.ts",
            "package.json",
            "tsconfig.json",
            "next.config.js",
            "postcss.config.js",
            "",
            "## Assets",
            "",
            "images/logo.png",
            "images/hero-bg.jpg",
            "",
            "CRITICAL RULES:",
            "- Each file path must start with app/, components/, styles/, lib/, or be a root config file.",
            "- Do NOT use src/ prefix.",
            "- Group related files under components/sections/.",
            "- Page files go under app/ using Next.js App Router conventions (app/page.tsx, app/about/page.tsx).",
            "- Include package.json, tsconfig.json, next.config.js, tailwind.config.ts, postcss.config.js.",
            "- List styles/globals.css for global styles.",
            "- List lib/utils.ts for utility functions.",
            "- Assets go under images/.",
            "- Do NOT output any text outside the file list.",
            "- Do NOT explain or comment on the files.",
        ]
        sections_list.append(
            "## Output Format Specification\n\n" + "\n".join(format_lines)
        )

        # -- Final Instructions --
        final_lines: List[str] = [
            "- Never hallucinate missing content.",
            "- Never invent missing sections.",
            "- Never replace extracted branding.",
        ]
        if "rules" in cat_names:
            final_lines.append(
                "- Never ignore rules.md — it contains the master rulebook."
            )
        final_lines.append(
            "- Always preserve WebsiteProfile integrity."
        )
        sections_list.append(
            "## Final Instructions\n\n" + "\n".join(final_lines)
        )

        content = "# Website Generation Manifest\n\n" + "\n\n".join(sections_list)
        content = sanitize_markdown(content)
        content = normalize_headings(content)
        content = normalize_spacing(content)

        if not validate_markdown(content):
            raise ValueError("output.md content validation failed — "
                             "missing heading or contains placeholder")

        wc = calculate_word_count(content)
        et = estimate_tokens(content)
        return MarkdownDocument(
            filename=CATEGORY_FILENAMES[MarkdownCategory.OUTPUT],
            title="Website Generation Manifest",
            category=MarkdownCategory.OUTPUT.value,
            priority=CATEGORY_PRIORITIES[MarkdownCategory.OUTPUT],
            content=content,
            version=MARKDOWN_PACKAGE_VERSION,
            generated_at=datetime.now(timezone.utc),
            word_count=wc,
            estimated_tokens=et,
        )

    def _generate_seo_rules(self) -> List[str]:
        """Generate deterministic SEO rules from extracted data only."""
        rules: List[str] = []
        seo = self.blueprint.seo

        if seo.page_title:
            rules.append(f"- Preserve exact page title: `{seo.page_title}`.")
        if seo.meta_description:
            rules.append(f"- Preserve meta description as detected.")
        if seo.focus_keywords:
            rules.append(f"- Target detected keywords: {', '.join(seo.focus_keywords)}.")
        if seo.https_enabled:
            rules.append("- Maintain HTTPS enforcement.")
        if seo.missing_title:
            rules.append("- Ensure every page has a unique `<title>` tag.")
        if seo.missing_meta_description:
            rules.append("- Ensure every page has a unique meta description.")
        if seo.missing_h1:
            rules.append("- Ensure every page has exactly one `<h1>` element.")

        return rules

    def _generate_brand_rules(self) -> List[str]:
        """Generate strict brand rules derived solely from extracted data.
        Returns an empty list if no rules can be grounded in real data."""
        rules: List[str] = []
        cols = self.blueprint.brand.brand_colors
        typo = self.blueprint.brand.typography_info
        cs = self.blueprint.brand.component_styles

        if cols and cols.primary:
            rules.append(f"- Never replace the primary color (`{cols.primary}`).")
        if cols and cols.secondary:
            rules.append(f"- Never replace the secondary color (`{cols.secondary}`).")

        if typo:
            if typo.primary_font and typo.heading_font:
                if typo.primary_font == typo.heading_font:
                    rules.append("- Use a single font family throughout the site.")
                else:
                    rules.append(f"- Use `{typo.primary_font}` for body text and "
                                 f"`{typo.heading_font}` for headings — do not introduce a third family.")
            if typo.weights_used:
                if len(typo.weights_used) <= 2:
                    rules.append("- Do not introduce font weights beyond the detected set.")
                else:
                    weights = sorted(typo.weights_used)
                    rules.append(f"- Restrict font weights to {', '.join(str(w) for w in weights)}.")

        if cs and cs.component_styles:
            btn = cs.component_styles.get("button", {})
            card = cs.component_styles.get("card", {})
            radii = set()
            for d in [btn, card]:
                r = d.get("border_radius") if d else None
                if r:
                    radii.add(r)
            if len(radii) == 1:
                rules.append(f"- Use a consistent `border-radius` of `{radii.pop()}` across all interactive elements.")
            elif len(radii) > 1:
                rules.append("- Keep border-radius consistent across buttons and cards.")

        return rules

    def build(self, category: MarkdownCategory) -> MarkdownDocument:
        """Build a single MarkdownDocument for one category."""
        raise NotImplementedError("Implemented in Phase 3.2")

    def build_content_md(self) -> MarkdownDocument:
        """Build the content.md document with verbatim source content."""
        snapshot = SourceWebsiteSnapshot.from_profile(self.blueprint)
        manifest = ManifestBuilder(self.blueprint).build()
        self._asset_manifest = manifest
        content = format_source_content(snapshot, manifest=manifest)
        content = sanitize_markdown(content)
        content = normalize_headings(content)
        content = normalize_spacing(content)

        if not validate_markdown(content):
            raise ValueError("content.md content validation failed — "
                             "missing heading or contains placeholder")

        wc = calculate_word_count(content)
        et = estimate_tokens(content)
        return MarkdownDocument(
            filename=CATEGORY_FILENAMES[MarkdownCategory.CONTENT],
            title="Source Website Content",
            category=MarkdownCategory.CONTENT.value,
            priority=CATEGORY_PRIORITIES[MarkdownCategory.CONTENT],
            content=content,
            version=MARKDOWN_PACKAGE_VERSION,
            generated_at=datetime.now(timezone.utc),
            word_count=wc,
            estimated_tokens=et,
        )

    def build_package(self) -> MarkdownPackage:
        """Build the full MarkdownPackage from the blueprint.

        Orchestrates all 12 build_*_md() methods in fixed order.
        Each builder runs independently wrapped in try/except.
        build_output_md() is always called last."""
        start_time = time.monotonic()
        logger.info("Started package generation")

        # ---- Define build order: (category_key, field_name, method_call) ----
        build_order = [
            ("system", "system_md", self.build_system_md),
            ("developer", "developer_md", self.build_developer_md),
            ("branding", "branding_md", self.build_branding_md),
            ("layout", "layout_md", self.build_layout_md),
            ("components", "components_md", self.build_components_md),
            ("animations", "animations_md", self.build_animations_md),
            ("seo", "seo_md", self.build_seo_md),
            ("performance", "performance_md", self.build_performance_md),
            ("accessibility", "accessibility_md", self.build_accessibility_md),
            ("assets", "assets_md", self.build_assets_md),
            ("rules", "rules_md", self.build_rules_md),
            ("content", "content_md", self.build_content_md),
        ]

        results: Dict[str, MarkdownDocument] = {}
        generated_docs: Dict[str, MarkdownDocument] = {}
        successful: List[str] = []
        failed: List[Dict[str, str]] = []

        def _fallback_doc(cat_key: str) -> MarkdownDocument:
            """Build a minimal zero-content fallback for failed builders."""
            return MarkdownDocument(
                filename="",
                title="",
                category="",
                priority=0,
                content="",
                word_count=0,
                estimated_tokens=0,
            )

        for cat_key, field_name, builder_fn in build_order:
            try:
                doc = builder_fn()
            except Exception as exc:
                msg = f"{type(exc).__name__}: {exc}"
                logger.warning("Failed to build %s: %s", cat_key, msg)
                failed.append({"category": cat_key, "error": msg})
                results[field_name] = _fallback_doc(cat_key)
                continue

            # Structural checks (not markdown content re-validation)
            if not doc.filename or not doc.category or not doc.content:
                msg = "Structural check failed: empty filename/category/content"
                logger.warning("Failed structural check for %s: %s", cat_key, msg)
                failed.append({"category": cat_key, "error": msg})
                results[field_name] = _fallback_doc(cat_key)
                continue
            if doc.word_count <= 0 and doc.content:
                msg = "Structural check failed: word_count is 0 despite non-empty content"
                logger.warning("Failed structural check for %s: %s", cat_key, msg)
                failed.append({"category": cat_key, "error": msg})
                results[field_name] = _fallback_doc(cat_key)
                continue

            results[field_name] = doc
            generated_docs[cat_key] = doc
            successful.append(cat_key)
            logger.info("Built %s.md (%d words)", cat_key, doc.word_count)

        # ---- Build output.md last (depends on previous results) ----
        try:
            output_doc = self.build_output_md(generated_docs)
            results["output_md"] = output_doc
            successful.append("output")
            logger.info("Built output.md (%d words)", output_doc.word_count)
        except Exception as exc:
            msg = f"{type(exc).__name__}: {exc}"
            logger.warning("Failed to build output: %s", msg)
            failed.append({"category": "output", "error": msg})
            results["output_md"] = _fallback_doc("output")

        # ---- Assemble MarkdownPackage ----
        package = MarkdownPackage(
            system_md=results.get("system_md", _fallback_doc("system")),
            developer_md=results.get("developer_md", _fallback_doc("developer")),
            branding_md=results.get("branding_md", _fallback_doc("branding")),
            layout_md=results.get("layout_md", _fallback_doc("layout")),
            components_md=results.get("components_md", _fallback_doc("components")),
            animations_md=results.get("animations_md", _fallback_doc("animations")),
            seo_md=results.get("seo_md", _fallback_doc("seo")),
            performance_md=results.get("performance_md", _fallback_doc("performance")),
            accessibility_md=results.get("accessibility_md", _fallback_doc("accessibility")),
            assets_md=results.get("assets_md", _fallback_doc("assets")),
            rules_md=results.get("rules_md", _fallback_doc("rules")),
            content_md=results.get("content_md", _fallback_doc("content")),
            output_md=results.get("output_md", _fallback_doc("output")),
        )

        # ---- Populate metadata ----
        all_docs = package.list_documents()
        total_tokens = sum(d.estimated_tokens for d in all_docs)
        total_words = sum(d.word_count for d in all_docs)
        duration = time.monotonic() - start_time

        bp = self.blueprint
        website_type = ""
        style = ""
        if bp.brand and bp.brand.design_language:
            website_type = bp.brand.design_language.design_language or ""
            style = website_type
        industry = bp.business.industry or ""

        package.metadata = MarkdownMetadata(
            version=MARKDOWN_PACKAGE_VERSION,
            generator_version=GENERATOR_VERSION,
            created_at=datetime.now(timezone.utc),
            website_type=website_type,
            industry=industry,
            style=style,
            estimated_total_tokens=total_tokens,
            generation_duration=duration,
            successful_documents=successful,
            failed_documents=failed,
            total_documents=13,
            total_words=total_words,
        )

        package.asset_manifest = self._asset_manifest

        logger.info(
            "Package generation complete: %d/13 successful, "
            "%d failed in %.2fs",
            len(successful), len(failed), duration,
        )

        return package

    def validate(self, package: MarkdownPackage) -> bool:
        """Validate a completed package (structure/content checks)."""
        raise NotImplementedError("Implemented in Phase 3.2")

    def export_directory(self, package: MarkdownPackage, output_path: str) -> str:
        return PackageExporter().export_folder(package, output_path)

    def export_zip(self, package: MarkdownPackage, output_path: str) -> str:
        return PackageExporter().export_zip(package, output_path)

    def export_single_file(self, package: MarkdownPackage, output_path: str) -> str:
        return PackageExporter().export_single_file(package, output_path)
