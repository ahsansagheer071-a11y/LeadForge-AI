import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.revoked_token import RevokedToken
from app.repositories.base import BaseRepository
from pydantic import BaseModel


class RevokedTokenCreate(BaseModel):
    token: str
    expires_at: datetime


class RevokedTokenUpdate(BaseModel):
    pass


class RevokedTokenRepository(BaseRepository[RevokedToken, RevokedTokenCreate, RevokedTokenUpdate]):
    """
    Repository for tracking blacklisted JWT tokens.
    """

    def __init__(self):
        super().__init__(RevokedToken)

    async def is_token_revoked(self, db: AsyncSession, token: str) -> bool:
        """
        Check if a JWT token exists in the blacklist database.
        """
        result = await db.execute(
            select(self.model).filter(self.model.token == token)
        )
        return result.scalars().first() is not None

    async def revoke_token(self, db: AsyncSession, token: str, expires_at: datetime) -> None:
        """
        Add a JWT token to the blacklist database.
        """
        # Ensure timezone-aware datetime is handled safely
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
            
        db_obj = self.model(
            token=token,
            expires_at=expires_at
        )
        db.add(db_obj)
        await db.flush()


# Instantiated revoked token repository instance
revoked_token_repository = RevokedTokenRepository()
