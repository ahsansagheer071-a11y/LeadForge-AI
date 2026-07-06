import logging
from typing import Dict, List, Optional

from app.services.markdown_engine.schemas import (
    DocumentStatistics,
    MarkdownDocument,
    MarkdownPackage,
    PackageStatisticsResult,
)

logger = logging.getLogger(__name__)

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


def _is_successful(doc: MarkdownDocument) -> bool:
    return doc.word_count > 0 and bool(doc.content)


class PackageStatistics:
    def calculate_document_statistics(
        self, document: MarkdownDocument
    ) -> DocumentStatistics:
        return DocumentStatistics(
            filename=document.filename or "",
            category=document.category or "",
            word_count=document.word_count,
            estimated_tokens=document.estimated_tokens,
            content_length=len(document.content),
            is_successful=_is_successful(document),
        )

    def calculate_category_statistics(
        self, package: MarkdownPackage
    ) -> Dict[str, DocumentStatistics]:
        field_to_category = {
            "system_md": "system",
            "developer_md": "developer",
            "branding_md": "branding",
            "layout_md": "layout",
            "components_md": "components",
            "animations_md": "animations",
            "seo_md": "seo",
            "performance_md": "performance",
            "accessibility_md": "accessibility",
            "assets_md": "assets",
            "rules_md": "rules",
            "output_md": "output",
        }
        breakdown: Dict[str, DocumentStatistics] = {}
        for field_name, cat_key in field_to_category.items():
            doc = getattr(package, field_name)
            breakdown[cat_key] = self.calculate_document_statistics(doc)
        return breakdown

    def calculate_package_statistics(
        self, package: MarkdownPackage
    ) -> PackageStatisticsResult:
        logger.info("Statistics calculation started")
        docs = package.list_documents()

        doc_stats = [self.calculate_document_statistics(d) for d in docs]
        successful = [s for s in doc_stats if s.is_successful]
        failed = [s for s in doc_stats if not s.is_successful]

        total_words = sum(s.word_count for s in doc_stats)
        total_tokens = sum(s.estimated_tokens for s in doc_stats)

        avg_words = 0.0
        if successful:
            avg_words = total_words / len(successful)

        largest: Optional[DocumentStatistics] = None
        smallest: Optional[DocumentStatistics] = None
        if successful:
            largest = max(successful, key=lambda s: s.word_count)
            smallest = min(successful, key=lambda s: s.word_count)

        category_breakdown = self.calculate_category_statistics(package)

        meta = package.metadata
        result = PackageStatisticsResult(
            total_documents=12,
            successful_documents=len(successful),
            failed_documents=len(failed),
            total_words=total_words,
            total_estimated_tokens=total_tokens,
            average_words_per_document=avg_words,
            largest_document=largest,
            smallest_document=smallest,
            category_breakdown=category_breakdown,
            generation_duration=meta.generation_duration if meta else 0.0,
            generated_at=meta.created_at if meta else None,
        )

        logger.info(
            "Statistics finished: %d/%d successful, %d words, %d tokens",
            len(successful),
            len(doc_stats),
            total_words,
            total_tokens,
        )
        return result
