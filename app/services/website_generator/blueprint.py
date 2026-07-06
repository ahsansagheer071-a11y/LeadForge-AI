import json
import logging
import re
from typing import Any, Dict, List, Optional

from app.services.website_generator.blueprint_schemas import (
    BlueprintAsset,
    BlueprintPage,
    WebsiteBlueprint,
)
from app.services.website_generator.schemas import GeneratedFile, WebsiteProject
from app.services.website_intelligence.schemas import CtaLink, SectionInfo

logger = logging.getLogger(__name__)

_SECTION_TYPE_MAP: Dict[str, str] = {
    "navbar": "navbar",
    "navigation": "navbar",
    "header": "navbar",
    "hero": "hero",
    "about": "about",
    "service": "services",
    "services": "services",
    "portfolio": "portfolio",
    "pricing": "pricing",
    "price": "pricing",
    "faq": "faq",
    "faqs": "faq",
    "testimonial": "testimonials",
    "testimonials": "testimonials",
    "reviews": "testimonials",
    "contact": "contact",
    "cta": "cta",
    "call_to_action": "cta",
    "call-to-action": "cta",
    "footer": "footer",
}


class BlueprintBuilder:
    def build(self, website_project: WebsiteProject) -> WebsiteBlueprint:
        logger.info(
            "BlueprintBuilder: Building website blueprint..."
        )

        project_name = website_project.project_name or "leadforge_ai_website"
        business_name = project_name.replace("_", " ").replace("-", " ").title()

        logger.info("Project: %s", project_name)

        metadata = self._build_metadata(website_project)
        pages = self._extract_pages(website_project.files)
        nav_sections, other_sections = self._classify_sections(
            website_project.files
        )
        navigation = self._build_navigation(nav_sections, pages)
        footer = self._build_footer(other_sections)
        sections = self._build_section_list(
            other_sections, nav_sections, pages
        )
        theme = self._build_theme(website_project.metadata)
        assets = self._extract_assets(website_project.assets)
        seo = self._build_seo(website_project.metadata)

        logger.info("Pages extracted: %d", len(pages))
        logger.info("Sections extracted: %d", len(sections))
        logger.info("Assets extracted: %d", len(assets))

        blueprint = WebsiteBlueprint(
            project_name=project_name,
            business_name=business_name,
            theme=theme,
            pages=pages,
            navigation=navigation,
            footer=footer,
            sections=sections,
            assets=assets,
            seo=seo,
            metadata=metadata,
        )

        logger.info(
            "BlueprintBuilder: Blueprint created successfully"
        )
        return blueprint

    @staticmethod
    def _build_metadata(project: WebsiteProject) -> Dict[str, Any]:
        return {
            "generation_id": project.generation_id,
            "version": project.version,
            "generated_at": project.generated_at.isoformat()
            if project.generated_at
            else None,
            "provider": project.metadata.get("provider", ""),
            "model": project.metadata.get("model", ""),
            "generation_time": project.metadata.get(
                "generation_time", 0.0
            ),
            "total_tokens": project.metadata.get("total_tokens"),
            "framework": project.framework,
        }

    @staticmethod
    def _extract_pages(
        files: List[GeneratedFile],
    ) -> List[BlueprintPage]:
        pages: List[BlueprintPage] = []
        seen_routes: set = set()
        for f in files:
            route = BlueprintBuilder._path_to_route(f.path)
            if route in seen_routes:
                continue
            if f.type == "page" or re.search(
                r"(?:^|/)pages/", f.path
            ) or re.match(r"^app/(.+/)?page\.[a-z]+$", f.path):
                page_name = BlueprintBuilder._path_to_page_name(f.path)
                seen_routes.add(route)
                pages.append(
                    BlueprintPage(
                        page_name=page_name,
                        route=route,
                        title=page_name.replace("_", " ").title(),
                    )
                )
        if not pages:
            pages.append(
                BlueprintPage(
                    page_name="index",
                    route="/",
                    title="Home",
                )
            )
        return pages

    @staticmethod
    def _classify_sections(
        files: List[GeneratedFile],
    ) -> tuple[List[GeneratedFile], List[GeneratedFile]]:
        nav_sections: List[GeneratedFile] = []
        other_sections: List[GeneratedFile] = []
        for f in files:
            if f.type != "react_component":
                continue
            name = BlueprintBuilder._path_to_component_name(
                f.path
            ).lower()
            section_type = _SECTION_TYPE_MAP.get(name, "")
            if section_type == "navbar":
                nav_sections.append(f)
            else:
                other_sections.append(f)
        return nav_sections, other_sections

    @staticmethod
    def _build_navigation(
        nav_sections: List[GeneratedFile],
        pages: List[BlueprintPage],
    ) -> Dict[str, Any]:
        links = [
            {"label": p.page_name.replace("_", " ").title(), "url": p.route}
            for p in pages
        ]
        is_sticky = len(nav_sections) > 0
        return {
            "links": links,
            "is_sticky": is_sticky,
            "has_navbar_component": len(nav_sections) > 0,
        }

    @staticmethod
    def _build_footer(
        other_sections: List[GeneratedFile],
    ) -> Dict[str, Any]:
        has_footer = any(
            _SECTION_TYPE_MAP.get(
                BlueprintBuilder._path_to_component_name(f.path).lower(),
                "",
            )
            == "footer"
            for f in other_sections
        )
        return {
            "has_footer_component": has_footer,
            "columns": 3,
            "show_newsletter": False,
        }

    @staticmethod
    def _build_section_list(
        other_sections: List[GeneratedFile],
        nav_sections: List[GeneratedFile],
        pages: List[BlueprintPage],
    ) -> List[SectionInfo]:
        seen_types: set = set()
        sections: List[SectionInfo] = []
        order = 0

        if nav_sections:
            sections.append(
                SectionInfo(
                    section_type="navbar",
                    order=order,
                    heading="Navigation",
                    description="Main navigation bar",
                )
            )
            order += 1
            seen_types.add("navbar")

        for f in other_sections:
            name = BlueprintBuilder._path_to_component_name(
                f.path
            ).lower()
            section_type = _SECTION_TYPE_MAP.get(name, "")
            if section_type and section_type not in seen_types:
                seen_types.add(section_type)
                sections.append(
                    SectionInfo(
                        section_type=section_type,
                        order=order,
                        heading=name.title(),
                        description=f"Content for {name} section",
                    )
                )
                order += 1

        if "footer" not in seen_types and any(
            _SECTION_TYPE_MAP.get(
                BlueprintBuilder._path_to_component_name(f.path).lower(),
                "",
            )
            == "footer"
            for f in other_sections
        ):
            sections.append(
                SectionInfo(
                    section_type="footer",
                    order=order,
                    heading="Footer",
                    description="Site footer",
                )
            )

        return sections

    @staticmethod
    def _build_theme(
        metadata: Dict[str, Any],
    ) -> Dict[str, str]:
        theme: Dict[str, str] = {}
        if "colors" in metadata and isinstance(
            metadata["colors"], dict
        ):
            theme.update(metadata["colors"])
        if "fonts" in metadata and isinstance(
            metadata["fonts"], dict
        ):
            theme.update(metadata["fonts"])
        return theme

    @staticmethod
    def _extract_assets(
        raw_assets: List[str],
    ) -> List[BlueprintAsset]:
        assets: List[BlueprintAsset] = []
        seen_refs: set = set()
        for raw in raw_assets:
            try:
                data = (
                    json.loads(raw) if isinstance(raw, str) else raw
                )
                ref = data.get("reference", "")
                if ref in seen_refs:
                    continue
                seen_refs.add(ref)
                assets.append(
                    BlueprintAsset(
                        filename=data.get("filename", ""),
                        asset_type=data.get("asset_type", "image"),
                        reference=ref,
                        metadata=data.get("metadata", {}),
                    )
                )
            except (json.JSONDecodeError, TypeError, KeyError):
                logger.warning(
                    "BlueprintBuilder: Skipping unparseable asset: %s",
                    str(raw)[:80],
                )
        return assets

    @staticmethod
    def _build_seo(
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "title": metadata.get("seo_title", ""),
            "description": metadata.get("seo_description", ""),
            "keywords": metadata.get("seo_keywords", []),
        }

    @staticmethod
    def _path_to_route(path: str) -> str:
        cleaned = path.replace("\\", "/")
        cleaned = re.sub(r"^src/", "", cleaned)
        cleaned = re.sub(r"^app/", "", cleaned)
        cleaned = re.sub(r"^pages/", "", cleaned)
        cleaned = re.sub(r"(?:/|^)page\.[a-z]+$", "", cleaned)
        cleaned = re.sub(r"\.[a-z]+$", "", cleaned)
        if cleaned == "index" or cleaned == "":
            return "/"
        cleaned = cleaned.replace("index", "")
        if cleaned.endswith("/"):
            cleaned = cleaned[:-1]
        return "/" + cleaned if not cleaned.startswith("/") else cleaned

    @staticmethod
    def _path_to_page_name(path: str) -> str:
        route = BlueprintBuilder._path_to_route(path)
        name = route.strip("/").replace("/", "_")
        return name if name else "index"

    @staticmethod
    def _path_to_component_name(path: str) -> str:
        parts = path.replace("\\", "/").split("/")
        filename = parts[-1] if parts else path
        name = re.sub(r"\.[a-z]+$", "", filename)
        # Strip "Section" suffix for section type matching
        name = re.sub(r"Section$", "", name, flags=re.IGNORECASE)
        return name
