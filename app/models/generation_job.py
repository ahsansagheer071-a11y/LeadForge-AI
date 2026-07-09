import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, Float, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

class GenerationJob(Base):
    """Persistent generation job record to survive backend restarts."""
    __tablename__ = "generation_jobs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4, index=True)
    job_id: Mapped[str] = mapped_column(String(64), index=True, unique=True, nullable=False)
    lead_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    progress: Mapped[str] = mapped_column(String(255), default="Queued", nullable=False)
    
    website_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    generation_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    preview_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    package_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    project_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    generation_time: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
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
    
    lead = relationship("Lead", backref="generation_jobs")
    user = relationship("User", backref="generation_jobs")

    __table_args__ = (
        Index(
            "ix_generation_jobs_active_per_lead",
            "lead_id",
            unique=True,
            postgresql_where=text("status IN ('pending', 'running')"),
        ),
    )


