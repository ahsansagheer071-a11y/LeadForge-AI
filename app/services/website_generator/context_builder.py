import uuid
from typing import Optional

from app.services.markdown_engine.schemas import MarkdownPackage
from app.services.website_generator.schemas import GenerationContext
from app.services.website_intelligence.schemas import WebsiteProfile


class ContextBuilder:
    def build(
        self,
        blueprint: WebsiteProfile,
        package: MarkdownPackage,
        generation_id: Optional[str] = None,
    ) -> GenerationContext:
        if generation_id is None:
            generation_id = uuid.uuid4().hex[:12]

        source_package_version = ""
        if package.metadata is not None:
            source_package_version = package.metadata.version

        return GenerationContext(
            system_context=package.system_md.content,
            developer_context=package.developer_md.content,
            branding_context=package.branding_md.content,
            content_context=package.content_md.content,
            layout_context=package.layout_md.content,
            components_context=package.components_md.content,
            animation_context=package.animations_md.content,
            seo_context=package.seo_md.content,
            performance_context=package.performance_md.content,
            accessibility_context=package.accessibility_md.content,
            assets_context=package.assets_md.content,
            rules_context=package.rules_md.content,
            output_context=package.output_md.content,
            generation_id=generation_id,
            source_package_version=source_package_version,
        )
