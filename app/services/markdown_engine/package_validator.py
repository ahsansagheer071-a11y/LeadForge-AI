import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from app.services.markdown_engine.constants import (
    CATEGORY_FILENAMES,
    CATEGORY_PRIORITIES,
    MarkdownCategory,
)
from app.services.markdown_engine.schemas import (
    DocumentValidationResult,
    MarkdownDocument,
    MarkdownPackage,
    PackageValidationResult,
)

logger = logging.getLogger(__name__)

# The expected generation order from build_package()
EXPECTED_GENERATION_ORDER: List[MarkdownCategory] = [
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

# All 12 field names on MarkdownPackage in expected order
PACKAGE_FIELD_NAMES: List[str] = [
    "system_md",
    "developer_md",
    "branding_md",
    "layout_md",
    "components_md",
    "animations_md",
    "seo_md",
    "performance_md",
    "accessibility_md",
    "assets_md",
    "rules_md",
    "output_md",
]

VALID_CATEGORY_VALUES: set = {c.value for c in MarkdownCategory}


class PackageValidator:
    def validate_package(self, package: MarkdownPackage) -> PackageValidationResult:
        start = time.monotonic()
        logger.info("Package validation started")

        result = PackageValidationResult()
        all_errors: List[str] = []
        all_warnings: List[str] = []

        if package.metadata is None:
            all_errors.append("package.metadata is None")
            result.valid = False
            result.validation_duration = time.monotonic() - start
            return result

        if not package.metadata.version:
            all_errors.append("metadata.version is empty")

        if package.metadata.created_at is None:
            all_errors.append("metadata.created_at is None")

        if package.metadata.total_documents != 12:
            all_errors.append(
                f"metadata.total_documents is {package.metadata.total_documents}, expected 12"
            )

        if package.metadata.generation_duration < 0:
            all_errors.append(
                f"metadata.generation_duration is negative ({package.metadata.generation_duration})"
            )

        docs = package.list_documents()
        result.documents_checked = len(docs)

        filenames_seen: Dict[str, int] = {}
        categories_seen: Dict[str, int] = {}

        for doc in docs:
            doc_result = self.validate_document(doc)
            if doc_result.valid:
                result.documents_passed += 1
                logger.info("  %s: PASS", doc.filename)
            else:
                result.documents_failed += 1
                logger.info("  %s: FAIL (%s)", doc.filename, "; ".join(doc_result.errors))

            all_errors.extend(doc_result.errors)
            all_warnings.extend(doc_result.warnings)

            if doc.filename:
                filenames_seen[doc.filename] = filenames_seen.get(doc.filename, 0) + 1
            if doc.category:
                categories_seen[doc.category] = categories_seen.get(doc.category, 0) + 1

        dup_filenames = [fn for fn, count in filenames_seen.items() if count > 1]
        if dup_filenames:
            result.duplicate_documents = dup_filenames
            for fn in dup_filenames:
                all_errors.append(f"Duplicate filename: {fn}")

        dup_categories = [cat for cat, count in categories_seen.items() if count > 1]
        if dup_categories:
            for cat in dup_categories:
                all_warnings.append(f"Duplicate category: {cat}")

        manifest_msgs = self.validate_manifest(package)
        if manifest_msgs:
            result.manifest_valid = False
            all_warnings.extend(manifest_msgs)

        order_msgs = self.validate_generation_order(package)
        if order_msgs:
            result.generation_order_valid = False
            all_warnings.extend(order_msgs)

        stat_msgs = self.validate_statistics(package)
        if stat_msgs:
            result.statistics_valid = False
            all_errors.extend(stat_msgs)

        logger.info("Validating version consistency across all documents")
        result.versions_consistent = self.validate_versions(package)
        if not result.versions_consistent:
            all_errors.append(
                "versions_consistent: one or more documents have a version "
                "that does not match the package metadata version"
            )

        logger.info("Validating timestamp consistency across all documents")
        result.timestamps_consistent = self.validate_timestamps(package)
        if not result.timestamps_consistent:
            all_errors.append(
                "timestamps_consistent: one or more documents have a generated_at "
                "timestamp outside the expected generation window"
            )

        result.errors = all_errors
        result.warnings = all_warnings
        has_dup_category = any("Duplicate category" in w for w in all_warnings)
        has_metadata_errors = any(
            e.startswith("metadata.")
            for e in all_errors
            if not e.startswith("content is empty")
        )
        result.valid = (
            result.documents_failed == 0
            and not result.duplicate_documents
            and not has_dup_category
            and result.manifest_valid
            and result.statistics_valid
            and result.versions_consistent
            and result.timestamps_consistent
            and not has_metadata_errors
        )

        result.validation_duration = time.monotonic() - start
        logger.info(
            "Validation finished: %d/%d passed, %d errors, %d warnings (%.3fs)",
            result.documents_passed,
            result.documents_checked,
            len(result.errors),
            len(result.warnings),
            result.validation_duration,
        )
        return result

    def validate_document(self, document: MarkdownDocument) -> DocumentValidationResult:
        errors: List[str] = []
        warnings: List[str] = []

        if not document.filename:
            errors.append("filename is empty")
        if not document.title:
            errors.append("title is empty")
        if not document.category:
            errors.append("category is empty")
        elif document.category not in VALID_CATEGORY_VALUES:
            errors.append(f"category '{document.category}' is not a valid MarkdownCategory")
        if not document.content:
            errors.append("content is empty — likely a fallback/failed document from build_package()")
        if not document.version:
            errors.append("version is empty")
        if document.generated_at is None:
            errors.append("generated_at is None")
        if document.word_count <= 0:
            errors.append(f"word_count is {document.word_count}, expected > 0")
        if document.estimated_tokens <= 0:
            errors.append(f"estimated_tokens is {document.estimated_tokens}, expected > 0")

        return DocumentValidationResult(
            filename=document.filename or "",
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            word_count=document.word_count,
            estimated_tokens=document.estimated_tokens,
        )

    def validate_manifest(self, package: MarkdownPackage) -> List[str]:
        warnings: List[str] = []
        output_content = package.output_md.content
        docs = package.list_documents()

        category_names: Dict[str, MarkdownDocument] = {}
        for doc in docs:
            if doc.category:
                category_names[doc.category] = doc
            if doc.filename:
                category_names[doc.filename] = doc

        for doc in docs:
            if doc is package.output_md:
                continue
            name = doc.filename or doc.category or "(unnamed)"
            refs = [doc.filename, doc.title, doc.category]
            mentioned = False
            for ref in refs:
                if ref and ref in output_content:
                    mentioned = True
                    break
            if not mentioned:
                warnings.append(
                    f"Document '{name}' not referenced in output.md content"
                )

        output_categories_in_content = set()
        valid_category_values = {c.value for c in MarkdownCategory}
        valid_filenames = set(CATEGORY_FILENAMES.values())
        for line in output_content.splitlines():
            for cat in valid_category_values:
                if cat.lower() in line.lower():
                    output_categories_in_content.add(cat)
            for fn in valid_filenames:
                if fn in line:
                    output_categories_in_content.add(fn)

        for doc in docs:
            if doc is package.output_md:
                continue
            if doc.category and doc.category not in output_categories_in_content:
                if doc.filename and doc.filename not in output_categories_in_content:
                    if doc.title and doc.title not in output_categories_in_content:
                        pass

        for doc in docs:
            if doc is package.output_md:
                continue
            name = doc.filename or doc.category or "(unnamed)"
            for cat_val in valid_category_values:
                if cat_val not in output_content and cat_val not in str(output_content):
                    pass

        return warnings

    def validate_generation_order(self, package: MarkdownPackage) -> List[str]:
        warnings: List[str] = []
        priorities_order = [
            cat for cat, _ in sorted(
                CATEGORY_PRIORITIES.items(), key=lambda x: x[1]
            )
        ]
        if priorities_order != EXPECTED_GENERATION_ORDER:
            warnings.append(
                "CATEGORY_PRIORITIES in constants.py does not match "
                "the expected build_package() generation order. "
                "MarkdownPackage does not record the actual generation "
                "sequence, so this proxy check is used as a best-effort "
                "validation. Expected order: "
                + ", ".join(c.value for c in EXPECTED_GENERATION_ORDER)
                + ". Priority order: "
                + ", ".join(c.value for c in priorities_order)
                + "."
            )
        return warnings

    def validate_metadata(self, package: MarkdownPackage) -> List[str]:
        errors: List[str] = []
        meta = package.metadata
        if meta is None:
            errors.append("package.metadata is None")
            return errors
        if not meta.version:
            errors.append("metadata.version is empty")
        if meta.created_at is None:
            errors.append("metadata.created_at is None")
        if meta.total_documents != 12:
            errors.append(
                f"metadata.total_documents is {meta.total_documents}, expected 12"
            )
        if meta.generation_duration < 0:
            errors.append(
                f"metadata.generation_duration is negative ({meta.generation_duration})"
            )
        return errors

    def validate_statistics(self, package: MarkdownPackage) -> List[str]:
        errors: List[str] = []
        meta = package.metadata
        docs = package.list_documents()

        actual_total_words = sum(d.word_count for d in docs)
        if meta.total_words != actual_total_words:
            errors.append(
                f"metadata.total_words is {meta.total_words}, "
                f"but sum of document word_counts is {actual_total_words}"
            )

        actual_total_tokens = sum(d.estimated_tokens for d in docs)
        if meta.estimated_total_tokens != actual_total_tokens:
            errors.append(
                f"metadata.estimated_total_tokens is {meta.estimated_total_tokens}, "
                f"but sum of document estimated_tokens is {actual_total_tokens}"
            )

        return errors

    def validate_versions(self, package: MarkdownPackage) -> bool:
        meta = package.metadata
        if meta is None:
            return False
        expected = meta.version
        if not expected:
            return False
        for doc in package.list_documents():
            if doc.version != expected:
                logger.info(
                    "Version mismatch: document %s has version '%s', expected '%s'",
                    doc.filename, doc.version, expected,
                )
                return False
        return True

    @staticmethod
    def _as_utc(dt: datetime) -> datetime:
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    def validate_timestamps(self, package: MarkdownPackage) -> bool:
        meta = package.metadata
        if meta is None or meta.created_at is None:
            return False
        created = self._as_utc(meta.created_at)
        duration = timedelta(seconds=max(meta.generation_duration, 0))
        tolerance = timedelta(seconds=1)
        window_start = created - duration - tolerance
        window_end = created + tolerance
        for doc in package.list_documents():
            ts = doc.generated_at
            if ts is None:
                logger.info(
                    "Timestamp null: document %s has no generated_at",
                    doc.filename,
                )
                return False
            ts_utc = self._as_utc(ts)
            if ts_utc < window_start or ts_utc > window_end:
                logger.info(
                    "Timestamp outside window: document %s generated_at %s "
                    "(UTC %s), expected between %s and %s",
                    doc.filename, ts, ts_utc, window_start, window_end,
                )
                return False
        return True
