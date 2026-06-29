import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.screenshot import Screenshot
from app.schemas.screenshot import ScreenshotCreate, ScreenshotUpdate
from app.repositories.base import BaseRepository


class ScreenshotRepository(BaseRepository[Screenshot, ScreenshotCreate, ScreenshotUpdate]):
    """
    Repository for Screenshot operations.
    """

    def __init__(self):
        super().__init__(Screenshot)

    async def get_by_lead_id(self, db: AsyncSession, lead_id: uuid.UUID) -> Optional[Screenshot]:
        """
        Fetch a screenshot entry by lead ID.
        """
        result = await db.execute(
            select(self.model).filter(self.model.lead_id == lead_id)
        )
        return result.scalars().first()


# Instantiated screenshot repository instance
screenshot_repository = ScreenshotRepository()
