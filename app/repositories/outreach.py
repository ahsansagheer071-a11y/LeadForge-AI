import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.outreach import Outreach
from app.schemas.outreach import OutreachCreate, OutreachUpdate
from app.repositories.base import BaseRepository


class OutreachRepository(BaseRepository[Outreach, OutreachCreate, OutreachUpdate]):
    """
    Repository for Outreach operations.
    """

    def __init__(self):
        super().__init__(Outreach)

    async def get_by_lead_id(self, db: AsyncSession, lead_id: uuid.UUID) -> Optional[Outreach]:
        """
        Fetch outreach templates by lead ID.
        """
        result = await db.execute(
            select(self.model).filter(self.model.lead_id == lead_id)
        )
        return result.scalars().first()


# Instantiated outreach repository instance
outreach_repository = OutreachRepository()
