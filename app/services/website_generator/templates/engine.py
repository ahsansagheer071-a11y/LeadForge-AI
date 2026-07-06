import logging
from typing import Optional, Tuple, Type

from app.services.website_generator.templates.base_template import BaseTemplate
from app.services.website_generator.templates.registry import TemplateRegistry
from app.services.website_intelligence.schemas import SectionInfo

logger = logging.getLogger(__name__)


class TemplateEngine:
    def __init__(self, registry: TemplateRegistry) -> None:
        self._registry = registry

    def render_section(self, section: SectionInfo) -> str:
        template_cls = self.get_template_for_section(section)
        if template_cls is None:
            raise ValueError(
                f"Unsupported section type: '{section.section_type}'"
            )
        template = template_cls()
        if not template.validate(section):
            raise ValueError(
                f"Invalid section data for type '{section.section_type}': "
                f"missing required fields in {section.model_dump(exclude_none=True)}"
            )
        return template.render(section)

    def render_section_with_validation(
        self, section: SectionInfo
    ) -> Tuple[str, bool]:
        try:
            source = self.render_section(section)
            return source, True
        except ValueError as e:
            logger.warning(
                "TemplateEngine: Validation failed for '%s': %s",
                section.section_type,
                e,
            )
            import traceback
            fallback = self._generate_fallback(section)
            return fallback, False

    def get_template_for_section(
        self, section: SectionInfo
    ) -> Optional[Type[BaseTemplate]]:
        return self._registry.get(section.section_type)

    def _generate_fallback(self, section: SectionInfo) -> str:
        cls_name = section.section_type.capitalize()
        return f"""import React from 'react';

export const {cls_name}Section: React.FC = () => {{
  return (
    <section className="w-full py-16">
      <div className="container px-4 md:px-6">
        <div className="space-y-4">
          <h2 className="text-3xl font-bold tracking-tight">{section.heading or cls_name}</h2>
          {f'<p class="text-muted-foreground">{{description}}</p>' if section.description else ''}
        </div>
      </div>
    </section>
  );
}};
"""

    @property
    def registry(self) -> TemplateRegistry:
        return self._registry
