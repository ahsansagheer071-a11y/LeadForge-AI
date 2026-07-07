import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.generated_website import GeneratedWebsite
from app.repositories.base import BaseRepository
from app.schemas.generated_website import GeneratedWebsiteCreate, GeneratedWebsiteUpdate


class GeneratedWebsiteRepository(
    BaseRepository[GeneratedWebsite, GeneratedWebsiteCreate, GeneratedWebsiteUpdate]
):
    def __init__(self) -> None:
        super().__init__(GeneratedWebsite)

    async def get_latest_by_lead_id(
        self,
        db: AsyncSession,
        *,
        lead_id: uuid.UUID,
    ) -> Optional[GeneratedWebsite]:
        result = await db.execute(
            select(self.model)
            .where(self.model.lead_id == lead_id)
            .order_by(self.model.created_at.desc())
            .limit(1)
        )
        return result.scalars().first()


generated_website_repository = GeneratedWebsiteRepository()
