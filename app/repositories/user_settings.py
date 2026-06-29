import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user_settings import UserSettings
from app.schemas.user_settings import UserSettingsCreate, UserSettingsUpdate
from app.repositories.base import BaseRepository


class UserSettingsRepository(BaseRepository[UserSettings, UserSettingsCreate, UserSettingsUpdate]):
    """
    Repository for UserSettings operations.
    """

    def __init__(self):
        super().__init__(UserSettings)

    async def get_by_user_id(self, db: AsyncSession, user_id: uuid.UUID) -> Optional[UserSettings]:
        """
        Fetch setting configuration by user ID.
        """
        result = await db.execute(
            select(self.model).filter(self.model.user_id == user_id)
        )
        return result.scalars().first()


# Instantiated user settings repository instance
user_settings_repository = UserSettingsRepository()
