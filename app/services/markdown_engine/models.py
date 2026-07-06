import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class MarkdownPackageMetadata(Base):
    """SQLAlchemy model persisting MarkdownPackage metadata for tracking and
    history. Full markdown content is file-based — only metadata is stored."""

    __tablename__ = "markdown_package_metadata"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    lead_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("leads.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    version: Mapped[str] = mapped_column(
        String(50), default="1.0.0", nullable=False,
    )
    generator_version: Mapped[str] = mapped_column(
        String(100), default="leadforge-markdown-engine-1.0.0", nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    website_type: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
    )
    industry: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
    )
    style: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
    )
    estimated_total_tokens: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False,
    )
    document_count: Mapped[int] = mapped_column(
        Integer, default=12, nullable=False,
    )
