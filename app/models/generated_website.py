import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.lead import Lead


class GeneratedWebsite(Base):
    """Persisted generated website tied to a lead-owned workflow."""

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4, index=True)
    lead_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("leads.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    generation_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    project_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    framework: Mapped[str] = mapped_column(String(50), default="static-html", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="generated", nullable=False)
    html: Mapped[str] = mapped_column(Text, nullable=False)
    preview_path: Mapped[str] = mapped_column(String(255), nullable=False)
    package_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    package_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    build_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    lead: Mapped["Lead"] = relationship("Lead", back_populates="generated_websites")
