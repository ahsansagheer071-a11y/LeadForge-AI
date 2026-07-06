import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.markdown_engine.models import MarkdownPackageMetadata
from app.services.markdown_engine.schemas import MarkdownMetadata


class MarkdownPackageRepository:
    """
    Repository for MarkdownPackageMetadata CRUD operations.
    Persists only metadata — full markdown content is file-based.
    """

    def __init__(self) -> None:
        self.model = MarkdownPackageMetadata

    async def save_metadata(
        self,
        db: AsyncSession,
        *,
        lead_id: uuid.UUID,
        metadata: MarkdownMetadata,
        document_count: int = 12,
    ) -> MarkdownPackageMetadata:
        """Create a metadata record for a generated package."""
        db_obj = self.model(
            lead_id=lead_id,
            version=metadata.version,
            generator_version=metadata.generator_version,
            created_at=metadata.created_at,
            website_type=metadata.website_type,
            industry=metadata.industry,
            style=metadata.style,
            estimated_total_tokens=metadata.estimated_total_tokens,
            document_count=document_count,
        )
        db.add(db_obj)
        await db.flush()
        return db_obj

    async def get_by_lead_id(
        self,
        db: AsyncSession,
        *,
        lead_id: uuid.UUID,
    ) -> Optional[MarkdownPackageMetadata]:
        """Retrieve the latest metadata record for a given lead."""
        result = await db.execute(
            select(self.model)
            .filter(self.model.lead_id == lead_id)
            .order_by(self.model.created_at.desc())
            .limit(1)
        )
        return result.scalars().first()

    async def list_by_lead_id(
        self,
        db: AsyncSession,
        *,
        lead_id: uuid.UUID,
    ) -> List[MarkdownPackageMetadata]:
        """List all metadata records for a given lead, newest first."""
        result = await db.execute(
            select(self.model)
            .filter(self.model.lead_id == lead_id)
            .order_by(self.model.created_at.desc())
        )
        return list(result.scalars().all())

    async def delete_by_lead_id(
        self,
        db: AsyncSession,
        *,
        lead_id: uuid.UUID,
    ) -> bool:
        """Delete all metadata records for a given lead."""
        records = await self.list_by_lead_id(db, lead_id=lead_id)
        if not records:
            return False
        for record in records:
            await db.delete(record)
        await db.flush()
        return True
