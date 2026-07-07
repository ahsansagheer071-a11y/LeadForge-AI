import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.lead_score import LeadScore
    from app.models.audit import Audit
    from app.models.screenshot import Screenshot
    from app.models.outreach import Outreach
    from app.models.generated_website import GeneratedWebsite


class Lead(Base):
    """
    SQLAlchemy model representing a scraped business lead containing only core business details.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # Business Profile Information
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    website: Mapped[Optional[str]] = mapped_column(
        String(2083),  # Maximum URL length limit
        nullable=True
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    address: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    rating: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )
    reviews_count: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )
    maps_url: Mapped[Optional[str]] = mapped_column(
        String(2083),
        nullable=True
    )
    
    # Discovery Fields (used for searching & filtering)
    city: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False
    )
    country: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False
    )
    industry: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False
    )
    
    # Status Pipeline State
    # e.g., "NEW", "SCRAPED", "ANALYZED", "OUTREACH_GENERATED", "CONTACTED"
    status: Mapped[str] = mapped_column(
        String(50),
        default="NEW",
        nullable=False
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
    user: Mapped["User"] = relationship(
        "User",
        back_populates="leads"
    )
    score: Mapped["LeadScore"] = relationship(
        "LeadScore",
        back_populates="lead",
        uselist=False,
        cascade="all, delete-orphan"
    )
    audit: Mapped["Audit"] = relationship(
        "Audit",
        back_populates="lead",
        uselist=False,
        cascade="all, delete-orphan"
    )
    screenshot: Mapped["Screenshot"] = relationship(
        "Screenshot",
        back_populates="lead",
        uselist=False,
        cascade="all, delete-orphan"
    )
    outreach: Mapped["Outreach"] = relationship(
        "Outreach",
        back_populates="lead",
        uselist=False,
        cascade="all, delete-orphan"
    )
    generated_websites: Mapped[list["GeneratedWebsite"]] = relationship(
        "GeneratedWebsite",
        back_populates="lead",
        cascade="all, delete-orphan"
    )
