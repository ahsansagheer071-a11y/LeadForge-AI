import logging
from datetime import datetime, timezone

from app.services.website_generator.blueprint_schemas import WebsiteBlueprint
from app.services.website_generator.renderers.file_generator import FileGenerator
from app.services.website_generator.schemas import GeneratedFile, WebsiteProject
from app.services.website_generator.templates.engine import TemplateEngine
from app.services.website_generator.templates.registry import TemplateRegistry
from app.services.website_generator.templates.templates import get_all_template_classes

logger = logging.getLogger(__name__)


class NextJSRenderer:
    def __init__(
        self,
        engine: TemplateEngine | None = None,
    ) -> None:
        if engine is not None:
            self._engine = engine
        else:
            registry = TemplateRegistry()
            registry.register_many(get_all_template_classes())
            self._engine = TemplateEngine(registry)
        self._file_generator = FileGenerator(self._engine)

    def render(self, blueprint: WebsiteBlueprint) -> WebsiteProject:
        logger.info("NextJSRenderer: Rendering Next.js project from blueprint...")
        logger.info("Project: %s", blueprint.project_name or blueprint.business_name)

        project_name = blueprint.project_name or "leadforge_ai_website"
        business_name = blueprint.business_name or "LeadForge"

        files: list[GeneratedFile] = []

        layout = self._file_generator.generate_layout(blueprint)
        files.append(layout)

        globals_css = self._file_generator.generate_globals_css(blueprint)
        files.append(globals_css)

        utils = self._file_generator.generate_utils()
        files.append(utils)

        tailwind_config = self._file_generator.generate_tailwind_config()
        files.append(tailwind_config)

        package_json = self._file_generator.generate_package_json()
        files.append(package_json)

        tsconfig = self._file_generator.generate_tsconfig()
        files.append(tsconfig)

        postcss = self._file_generator.generate_postcss_config()
        files.append(postcss)

        next_config = self._file_generator.generate_next_config()
        files.append(next_config)

        seen_section_types: set = set()
        for section in blueprint.sections:
            st = section.section_type
            if st in seen_section_types:
                continue
            seen_section_types.add(st)
            component = self._file_generator.generate_section_component(
                section, business_name
            )
            if component:
                files.append(component)

        for page in blueprint.pages:
            page_file = self._file_generator.generate_page(blueprint, page)
            files.append(page_file)

        asset_files = self._file_generator.generate_asset_files(blueprint)
        files.extend(asset_files)

        total_size = sum(f.size for f in files)

        logger.info("Files generated: %d", len(files))
        logger.info("Total size: %d bytes", total_size)

        generation_id = blueprint.metadata.get("generation_id", "")
        version = blueprint.metadata.get("version", "1.0.0")
        generated_at_str = blueprint.metadata.get("generated_at")
        if generated_at_str:
            try:
                generated_at = datetime.fromisoformat(generated_at_str)
            except (ValueError, TypeError):
                generated_at = datetime.now(timezone.utc)
        else:
            generated_at = datetime.now(timezone.utc)

        import json as _json
        assets_json = [
            _json.dumps({"filename": a.filename, "asset_type": a.asset_type, "reference": a.reference})
            for a in blueprint.assets
        ]

        project = WebsiteProject(
            project_name=project_name,
            framework="nextjs",
            generation_id=generation_id,
            version=version,
            generated_at=generated_at,
            files=files,
            assets=assets_json,
            metadata={
                "provider": blueprint.metadata.get("provider", ""),
                "model": blueprint.metadata.get("model", ""),
                "generation_time": blueprint.metadata.get("generation_time", 0.0),
                "framework": "nextjs",
                "total_files": len(files),
                "total_size": total_size,
            },
            statistics={
                "total_files": len(files),
                "total_size_bytes": total_size,
                "sections_rendered": len(seen_section_types),
                "pages_rendered": len(blueprint.pages),
            },
        )

        logger.info("NextJSRenderer: Render complete")
        return project
