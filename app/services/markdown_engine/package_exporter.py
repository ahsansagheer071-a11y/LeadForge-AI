import json
import logging
import os
import tempfile
import zipfile
from typing import List

from app.services.markdown_engine.constants import CATEGORY_FILENAMES, MarkdownCategory
from app.services.markdown_engine.schemas import MarkdownDocument, MarkdownPackage

logger = logging.getLogger(__name__)

EXPORT_DOC_ORDER: List[MarkdownCategory] = [
    MarkdownCategory.SYSTEM,
    MarkdownCategory.DEVELOPER,
    MarkdownCategory.BRANDING,
    MarkdownCategory.LAYOUT,
    MarkdownCategory.COMPONENTS,
    MarkdownCategory.ANIMATIONS,
    MarkdownCategory.SEO,
    MarkdownCategory.PERFORMANCE,
    MarkdownCategory.ACCESSIBILITY,
    MarkdownCategory.ASSETS,
    MarkdownCategory.RULES,
    MarkdownCategory.OUTPUT,
]

FIELD_NAMES: List[str] = [
    "system_md", "developer_md", "branding_md", "layout_md",
    "components_md", "animations_md", "seo_md", "performance_md",
    "accessibility_md", "assets_md", "rules_md", "output_md",
]


class PackageExporter:
    def _write_documents(
        self, package: MarkdownPackage, output_dir: str
    ) -> None:
        os.makedirs(output_dir, exist_ok=True)
        for field_name in FIELD_NAMES:
            doc: MarkdownDocument = getattr(package, field_name)
            filename = doc.filename or "unnamed.md"
            filepath = os.path.join(output_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(doc.content)

    def export_folder(self, package: MarkdownPackage, output_path: str) -> str:
        logger.info("Export folder started: %s", output_path)
        self._write_documents(package, output_path)
        logger.info("Export folder finished: %s", output_path)
        return os.path.abspath(output_path)

    def export_zip(self, package: MarkdownPackage, output_path: str) -> str:
        logger.info("Export zip started: %s", output_path)
        with tempfile.TemporaryDirectory(prefix="leadforge_export_") as tmpdir:
            self._write_documents(package, tmpdir)
            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for field_name in FIELD_NAMES:
                    doc: MarkdownDocument = getattr(package, field_name)
                    filename = doc.filename or "unnamed.md"
                    filepath = os.path.join(tmpdir, filename)
                    zf.write(filepath, arcname=filename)
        logger.info("Export zip finished: %s", output_path)
        return os.path.abspath(output_path)

    def export_manifest_json(self, package: MarkdownPackage, output_path: str) -> str:
        logger.info("Export manifest JSON started: %s", output_path)
        entries = []
        for field_name in FIELD_NAMES:
            doc: MarkdownDocument = getattr(package, field_name)
            entries.append({
                "filename": doc.filename,
                "category": doc.category,
                "version": doc.version,
                "word_count": doc.word_count,
                "estimated_tokens": doc.estimated_tokens,
                "generated_at": doc.generated_at.isoformat() if doc.generated_at else None,
            })
        manifest = {
            "package_version": package.metadata.version if package.metadata else "",
            "generator_version": package.metadata.generator_version if package.metadata else "",
            "generated_at": package.metadata.created_at.isoformat() if package.metadata and package.metadata.created_at else None,
            "total_documents": 12,
            "documents": entries,
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        logger.info("Export manifest JSON finished: %s", output_path)
        return os.path.abspath(output_path)

    def export_single_file(self, package: MarkdownPackage, output_path: str) -> str:
        logger.info("Export single file started: %s", output_path)
        parts: List[str] = []
        for cat, field_name in zip(EXPORT_DOC_ORDER, FIELD_NAMES):
            doc: MarkdownDocument = getattr(package, field_name)
            heading = doc.category or cat.value
            display = f"{heading}: {doc.filename}" if doc.filename else heading
            separator = f"\n\n---\n\n# {display}\n\n"
            parts.append(separator)
            parts.append(doc.content)

        combined = "".join(parts).lstrip("\n")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(combined)
        logger.info("Export single file finished: %s", output_path)
        return os.path.abspath(output_path)
