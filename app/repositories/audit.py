import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.audit import Audit
from app.schemas.audit import AuditCreate, AuditUpdate
from app.repositories.base import BaseRepository


class AuditRepository(BaseRepository[Audit, AuditCreate, AuditUpdate]):
    """
    Repository for Audit operations.
    """

    def __init__(self):
        super().__init__(Audit)

    async def get_by_lead_id(self, db: AsyncSession, lead_id: uuid.UUID) -> Optional[Audit]:
        """
        Fetch an audit entry by lead ID.
        """
        result = await db.execute(
            select(self.model).filter(self.model.lead_id == lead_id)
        )
        return result.scalars().first()


# Instantiated audit repository instance
audit_repository = AuditRepository()
