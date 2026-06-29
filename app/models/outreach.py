import uuid
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.lead import Lead


class Outreach(Base):
    """
    SQLAlchemy model representing the personalized AI-generated outreach templates for a lead.
    """
    __tablename__ = "outreaches"

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
    
    # Generated Copy Contents
    email_subject: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    cold_email: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    followup_email: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    linkedin_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    whatsapp_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    short_cta: Mapped[Optional[str]] = mapped_column(
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
        back_populates="outreach"
    )
