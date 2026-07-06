from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.services.markdown_engine.constants import (
    MARKDOWN_PACKAGE_VERSION,
    GENERATOR_VERSION,
    CATEGORY_PRIORITIES,
    MarkdownCategory,
)


class MarkdownDocument(BaseModel):
    filename: str
    title: str
    category: str
    priority: int
    content: str
    version: str = MARKDOWN_PACKAGE_VERSION
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    word_count: int = 0
    estimated_tokens: int = 0

    model_config = ConfigDict(from_attributes=True)


class MarkdownMetadata(BaseModel):
    version: str = MARKDOWN_PACKAGE_VERSION
    generator_version: str = GENERATOR_VERSION
    created_at: datetime = Field(default_factory=datetime.utcnow)
    website_type: str = ""
    industry: str = ""
    style: str = ""
    estimated_total_tokens: int = 0
    generation_duration: float = 0.0
    successful_documents: List[str] = Field(default_factory=list)
    failed_documents: List[Dict[str, str]] = Field(default_factory=list)
    total_documents: int = 12
    total_words: int = 0

    model_config = ConfigDict(from_attributes=True)


class MarkdownPackage(BaseModel):
    system_md: MarkdownDocument = Field(default_factory=lambda: MarkdownDocument(
        filename="00-system.md", title="System Rules", category=MarkdownCategory.SYSTEM.value,
        priority=CATEGORY_PRIORITIES[MarkdownCategory.SYSTEM],
        content="", word_count=0, estimated_tokens=0,
    ))
    developer_md: MarkdownDocument = Field(default_factory=lambda: MarkdownDocument(
        filename="01-developer.md", title="Developer Guide", category=MarkdownCategory.DEVELOPER.value,
        priority=CATEGORY_PRIORITIES[MarkdownCategory.DEVELOPER],
        content="", word_count=0, estimated_tokens=0,
    ))
    branding_md: MarkdownDocument = Field(default_factory=lambda: MarkdownDocument(
        filename="02-branding.md", title="Brand Identity", category=MarkdownCategory.BRANDING.value,
        priority=CATEGORY_PRIORITIES[MarkdownCategory.BRANDING],
        content="", word_count=0, estimated_tokens=0,
    ))
    layout_md: MarkdownDocument = Field(default_factory=lambda: MarkdownDocument(
        filename="03-layout.md", title="Layout Structure", category=MarkdownCategory.LAYOUT.value,
        priority=CATEGORY_PRIORITIES[MarkdownCategory.LAYOUT],
        content="", word_count=0, estimated_tokens=0,
    ))
    components_md: MarkdownDocument = Field(default_factory=lambda: MarkdownDocument(
        filename="04-components.md", title="Component Library", category=MarkdownCategory.COMPONENTS.value,
        priority=CATEGORY_PRIORITIES[MarkdownCategory.COMPONENTS],
        content="", word_count=0, estimated_tokens=0,
    ))
    animations_md: MarkdownDocument = Field(default_factory=lambda: MarkdownDocument(
        filename="05-animations.md", title="Animation System", category=MarkdownCategory.ANIMATIONS.value,
        priority=CATEGORY_PRIORITIES[MarkdownCategory.ANIMATIONS],
        content="", word_count=0, estimated_tokens=0,
    ))
    seo_md: MarkdownDocument = Field(default_factory=lambda: MarkdownDocument(
        filename="06-seo.md", title="SEO Configuration", category=MarkdownCategory.SEO.value,
        priority=CATEGORY_PRIORITIES[MarkdownCategory.SEO],
        content="", word_count=0, estimated_tokens=0,
    ))
    performance_md: MarkdownDocument = Field(default_factory=lambda: MarkdownDocument(
        filename="07-performance.md", title="Performance Targets", category=MarkdownCategory.PERFORMANCE.value,
        priority=CATEGORY_PRIORITIES[MarkdownCategory.PERFORMANCE],
        content="", word_count=0, estimated_tokens=0,
    ))
    accessibility_md: MarkdownDocument = Field(default_factory=lambda: MarkdownDocument(
        filename="08-accessibility.md", title="Accessibility Requirements",
        category=MarkdownCategory.ACCESSIBILITY.value,
        priority=CATEGORY_PRIORITIES[MarkdownCategory.ACCESSIBILITY],
        content="", word_count=0, estimated_tokens=0,
    ))
    assets_md: MarkdownDocument = Field(default_factory=lambda: MarkdownDocument(
        filename="09-assets.md", title="Asset Management", category=MarkdownCategory.ASSETS.value,
        priority=CATEGORY_PRIORITIES[MarkdownCategory.ASSETS],
        content="", word_count=0, estimated_tokens=0,
    ))
    rules_md: MarkdownDocument = Field(default_factory=lambda: MarkdownDocument(
        filename="10-rules.md", title="Coding Standards", category=MarkdownCategory.RULES.value,
        priority=CATEGORY_PRIORITIES[MarkdownCategory.RULES],
        content="", word_count=0, estimated_tokens=0,
    ))
    output_md: MarkdownDocument = Field(default_factory=lambda: MarkdownDocument(
        filename="11-output.md", title="Output Requirements", category=MarkdownCategory.OUTPUT.value,
        priority=CATEGORY_PRIORITIES[MarkdownCategory.OUTPUT],
        content="", word_count=0, estimated_tokens=0,
    ))
    metadata: MarkdownMetadata = Field(default_factory=MarkdownMetadata)

    model_config = ConfigDict(from_attributes=True)

    def list_documents(self) -> List[MarkdownDocument]:
        return [
            self.system_md, self.developer_md, self.branding_md,
            self.layout_md, self.components_md, self.animations_md,
            self.seo_md, self.performance_md, self.accessibility_md,
            self.assets_md, self.rules_md, self.output_md,
        ]


class DocumentValidationResult(BaseModel):
    filename: str
    valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    word_count: int = 0
    estimated_tokens: int = 0

    model_config = ConfigDict(from_attributes=True)


class PackageValidationResult(BaseModel):
    valid: bool = False
    documents_checked: int = 0
    documents_passed: int = 0
    documents_failed: int = 0
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    missing_documents: List[str] = Field(default_factory=list)
    duplicate_documents: List[str] = Field(default_factory=list)
    generation_order_valid: bool = True
    manifest_valid: bool = True
    statistics_valid: bool = True
    versions_consistent: bool = True
    timestamps_consistent: bool = True
    validation_duration: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class DocumentStatistics(BaseModel):
    filename: str
    category: str
    word_count: int = 0
    estimated_tokens: int = 0
    content_length: int = 0
    is_successful: bool = False

    model_config = ConfigDict(from_attributes=True)


class PackageStatisticsResult(BaseModel):
    total_documents: int = 12
    successful_documents: int = 0
    failed_documents: int = 0
    total_words: int = 0
    total_estimated_tokens: int = 0
    average_words_per_document: float = 0.0
    largest_document: Optional[DocumentStatistics] = None
    smallest_document: Optional[DocumentStatistics] = None
    category_breakdown: Dict[str, DocumentStatistics] = Field(default_factory=dict)
    generation_duration: float = 0.0
    generated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
