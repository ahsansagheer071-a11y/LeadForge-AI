"""Legacy template registry — delegates to the new templates/ system.

This module is kept for backward compatibility.
All new code should import from app.services.website_generator.templates.
"""

import logging
from typing import Callable, Dict, List, Optional

from app.services.website_generator.templates.engine import TemplateEngine
from app.services.website_generator.templates.registry import (
    TemplateRegistry as _TemplateRegistry,
)
from app.services.website_generator.templates.templates import (
    get_all_template_classes,
)

logger = logging.getLogger(__name__)


class TemplateRegistry:
    """Backward-compatible wrapper that delegates to the new template system."""

    def __init__(self) -> None:
        self._new_registry = _TemplateRegistry()
        self._new_registry.register_many(get_all_template_classes())
        self._engine = TemplateEngine(self._new_registry)
        self._templates: Dict[str, Callable[..., str]] = {}

    def register(self, section_type: str, template: Callable[..., str]) -> None:
        self._templates[section_type] = template
        logger.debug(
            "LegacyRegistry: Registered function template for '%s'", section_type
        )

    def get_template(self, section_type: str) -> Optional[Callable[..., str]]:
        func = self._templates.get(section_type)
        if func:
            return func
        if self._new_registry.has(section_type):
            from app.services.website_intelligence.schemas import SectionInfo

            def wrapper(section: Optional[SectionInfo] = None) -> str:
                dummy = SectionInfo(
                    section_type=section_type,
                    heading=section_type.capitalize(),
                )
                return self._engine.render_section(dummy)

            return wrapper
        return None

    def has_template(self, section_type: str) -> bool:
        return (
            section_type in self._templates
            or self._new_registry.has(section_type)
        )

    def list_supported_types(self) -> List[str]:
        legacy = list(self._templates.keys())
        new = self._new_registry.list_supported()
        return list(dict.fromkeys(legacy + new))

    def register_all(self, templates: Dict[str, Callable[..., str]]) -> None:
        for section_type, template in templates.items():
            self.register(section_type, template)


def create_default_registry() -> TemplateRegistry:
    return TemplateRegistry()
