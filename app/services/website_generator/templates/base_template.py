from abc import ABC, abstractmethod
from typing import List

from app.services.website_intelligence.schemas import CtaLink, SectionInfo


class BaseTemplate(ABC):
    @abstractmethod
    def render(self, section: SectionInfo) -> str:
        ...

    @abstractmethod
    def validate(self, section: SectionInfo) -> bool:
        ...

    @abstractmethod
    def supported_section_type(self) -> str:
        ...

    def get_component_name(self, section_type: str) -> str:
        overrides = {"cta": "CTA", "faq": "FAQ"}
        base = overrides.get(section_type, section_type.capitalize())
        return f"{base}Section"

    def render_props(self, section: SectionInfo) -> str:
        lines: List[str] = [
            "interface Props {",
        ]
        if section.heading is not None:
            lines.append("  heading?: string;")
        if section.subheading is not None:
            lines.append("  subheading?: string;")
        if section.description is not None:
            lines.append("  description?: string;")
        if section.buttons:
            lines.append("  buttons?: Array<{ text: string; url: string }>;")
        if section.images:
            lines.append("  images?: string[];")
        lines.append("}")
        return "\n".join(lines)

    def render_content(self, section: SectionInfo) -> str:
        parts: List[str] = []
        if section.heading:
            parts.append(f"<h2>{section.heading}</h2>")
        if section.description:
            parts.append(f"<p>{section.description}</p>")
        return "\n".join(parts)

    @staticmethod
    def _format_buttons(buttons: List[CtaLink]) -> str:
        items = ", ".join(
            f'{{text: "{b.text}", url: "{b.url}"}}' for b in buttons
        )
        return f"[{items}]"
