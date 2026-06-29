import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from sqlalchemy import DateTime, ForeignKey, String, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class UserSettings(Base):
    """
    SQLAlchemy model representing custom configurations for API credentials
    provided by individual agency users. Can override system-wide keys.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False
    )
    
    # Custom API Credentials (encrypted/stored securely)
    gemini_api_key: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    serpapi_key: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    cloudinary_cloud_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    cloudinary_api_key: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    cloudinary_api_secret: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    
    # Preferences
    theme: Mapped[str] = mapped_column(
        String(20),
        default="system",
        nullable=False
    )
    email_notifications: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    default_page_size: Mapped[int] = mapped_column(
        Integer,
        default=10,
        nullable=False
    )
    default_sorting: Mapped[str] = mapped_column(
        String(50),
        default="created_at_desc",
        nullable=False
    )
    language: Mapped[str] = mapped_column(
        String(20),
        default="en",
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
        back_populates="settings"
    )
