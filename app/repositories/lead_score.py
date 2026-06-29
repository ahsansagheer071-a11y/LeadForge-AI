import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.lead_score import LeadScore
from app.schemas.lead_score import LeadScoreCreate, LeadScoreUpdate
from app.repositories.base import BaseRepository


class LeadScoreRepository(BaseRepository[LeadScore, LeadScoreCreate, LeadScoreUpdate]):
    """
    Repository for LeadScore operations.
    """

    def __init__(self):
        super().__init__(LeadScore)

    async def get_by_lead_id(self, db: AsyncSession, lead_id: uuid.UUID) -> Optional[LeadScore]:
        """
        Fetch a score entry by lead ID.
        """
        result = await db.execute(
            select(self.model).filter(self.model.lead_id == lead_id)
        )
        return result.scalars().first()


# Instantiated lead score repository instance
lead_score_repository = LeadScoreRepository()
