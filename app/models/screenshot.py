import uuid
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.lead import Lead


class Screenshot(Base):
    """
    SQLAlchemy model representing local and Cloudinary details for website screenshots.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    lead_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("leads.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False
    )
    
    # Desktop
    desktop_local_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    desktop_cloudinary_url: Mapped[Optional[str]] = mapped_column(String(2083), nullable=True)
    desktop_public_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Mobile
    mobile_local_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    mobile_cloudinary_url: Mapped[Optional[str]] = mapped_column(String(2083), nullable=True)
    mobile_public_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Full Page
    full_page_local_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    full_page_cloudinary_url: Mapped[Optional[str]] = mapped_column(String(2083), nullable=True)
    full_page_public_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    lead: Mapped["Lead"] = relationship(
        "Lead",
        back_populates="screenshot"
    )
