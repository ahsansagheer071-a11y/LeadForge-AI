import uuid
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.lead import Lead


class LeadScore(Base):
    """
    SQLAlchemy model representing scores computed by AI and scraping performance checks.
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
    
    # AI Scores (0 - 100)
    overall_score: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    seo_score: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    ux_score: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    branding_score: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    trust_score: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    conversion_score: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    
    # Lead classification category
    # "Hot Lead" (90-100), "Warm Lead" (70-89), "Cold Lead" (0-69)
    category: Mapped[str] = mapped_column(
        String(50),
        default="Cold Lead",
        nullable=False
    )

    # Score explanation
    explanation: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

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
        back_populates="score"
    )
