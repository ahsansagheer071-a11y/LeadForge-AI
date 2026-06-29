import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.security import verify_password, hash_password
from app.core.exceptions import ValidationException, NotFoundException
from app.models.user import User
from app.models.lead import Lead
from app.models.user_settings import UserSettings
from app.repositories.user import user_repository
from app.repositories.user_settings import user_settings_repository
from app.schemas.user import UserResponse, UserProfileUpdate, ChangePasswordRequest
from app.schemas.user_settings import UserSettingsResponse, UserPreferencesUpdate, AccountSummaryResponse

class SettingsService:
    async def get_profile(self, user: User) -> UserResponse:
        return UserResponse.model_validate(user)

    async def update_profile(self, db: AsyncSession, user: User, data: UserProfileUpdate) -> UserResponse:
        updated_user = await user_repository.update(db, db_obj=user, obj_in=data)
        return UserResponse.model_validate(updated_user)

    async def change_password(self, db: AsyncSession, user: User, data: ChangePasswordRequest) -> None:
        if not verify_password(data.current_password, user.hashed_password):
            raise ValidationException("Incorrect current password")
        
        # We don't implement full strength validation here, but we can do basic length
        if len(data.new_password) < 8:
            raise ValidationException("Password must be at least 8 characters long")
            
        hashed_password = hash_password(data.new_password)
        await user_repository.update(db, db_obj=user, obj_in={"hashed_password": hashed_password})
        # Note: Previous tokens remain valid unless token blacklisting/jti tracking is implemented in the auth system.

    async def get_preferences(self, db: AsyncSession, user_id: uuid.UUID) -> UserSettingsResponse:
        settings = await user_settings_repository.get_by_user_id(db, user_id=user_id)
        if not settings:
            # Create default settings if they don't exist
            settings = UserSettings(user_id=user_id)
            db.add(settings)
            await db.flush()
        return UserSettingsResponse.from_orm_model(settings)

    async def update_preferences(
        self, db: AsyncSession, user_id: uuid.UUID, data: UserPreferencesUpdate
    ) -> UserSettingsResponse:
        settings = await user_settings_repository.get_by_user_id(db, user_id=user_id)
        if not settings:
            # Should theoretically exist, but we handle it just in case
            raise NotFoundException("User settings not found")
        
        updated_settings = await user_settings_repository.update(db, db_obj=settings, obj_in=data)
        return UserSettingsResponse.from_orm_model(updated_settings)

    async def get_account_summary(self, db: AsyncSession, user: User) -> AccountSummaryResponse:
        # Get counts
        total_leads_q = select(func.count(Lead.id)).where(Lead.user_id == user.id)
        total_leads = (await db.execute(total_leads_q)).scalar() or 0
        
        audits_q = select(func.count(Lead.id)).where(
            Lead.user_id == user.id, 
            Lead.status.in_(["ANALYZED", "OUTREACH_READY", "CONTACTED", "CLOSED"])
        )
        total_audits = (await db.execute(audits_q)).scalar() or 0
        
        outreach_q = select(func.count(Lead.id)).join(Lead.outreach).where(Lead.user_id == user.id)
        total_outreach = (await db.execute(outreach_q)).scalar() or 0
        
        return AccountSummaryResponse(
            user_info=UserResponse.model_validate(user),
            total_leads=total_leads,
            total_audits=total_audits,
            total_outreach=total_outreach,
            account_created_at=user.created_at
        )

settings_service = SettingsService()
