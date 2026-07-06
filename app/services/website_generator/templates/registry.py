import logging
from typing import Dict, List, Optional, Type

from app.services.website_generator.templates.base_template import BaseTemplate

logger = logging.getLogger(__name__)


class TemplateRegistry:
    def __init__(self) -> None:
        self._templates: Dict[str, Type[BaseTemplate]] = {}

    def register(self, section_type: str, template_class: Type[BaseTemplate]) -> None:
        if not issubclass(template_class, BaseTemplate):
            raise TypeError(
                f"Template class {template_class.__name__} must be a subclass of BaseTemplate"
            )
        if section_type in self._templates:
            raise ValueError(
                f"Template already registered for section type '{section_type}'"
            )
        self._templates[section_type] = template_class
        logger.debug(
            "TemplateRegistry: Registered '%s' -> %s",
            section_type,
            template_class.__name__,
        )

    def get(self, section_type: str) -> Optional[Type[BaseTemplate]]:
        return self._templates.get(section_type)

    def has(self, section_type: str) -> bool:
        return section_type in self._templates

    def list_supported(self) -> List[str]:
        return list(self._templates.keys())

    def get_all(self) -> Dict[str, Type[BaseTemplate]]:
        return dict(self._templates)

    def register_many(
        self, mappings: Dict[str, Type[BaseTemplate]]
    ) -> None:
        for section_type, template_class in mappings.items():
            self.register(section_type, template_class)
