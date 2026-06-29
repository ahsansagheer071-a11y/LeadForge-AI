from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.response import StandardResponse
from app.schemas.user import UserResponse, UserProfileUpdate, ChangePasswordRequest
from app.schemas.user_settings import UserSettingsResponse, UserPreferencesUpdate, AccountSummaryResponse
from app.services.settings import settings_service

router = APIRouter()

@router.get(
    "/profile",
    response_model=StandardResponse[UserResponse],
    summary="Get user profile",
)
async def get_profile(
    current_user: User = Depends(get_current_user),
):
    data = await settings_service.get_profile(user=current_user)
    return StandardResponse(success=True, message="Profile retrieved successfully.", data=data)

@router.patch(
    "/profile",
    response_model=StandardResponse[UserResponse],
    summary="Update user profile",
)
async def update_profile(
    payload: UserProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = await settings_service.update_profile(db=db, user=current_user, data=payload)
    return StandardResponse(success=True, message="Profile updated successfully.", data=data)

@router.patch(
    "/change-password",
    response_model=StandardResponse[None],
    summary="Change user password",
)
async def change_password(
    payload: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await settings_service.change_password(db=db, user=current_user, data=payload)
    return StandardResponse(success=True, message="Password changed successfully.", data=None)

@router.get(
    "/preferences",
    response_model=StandardResponse[UserSettingsResponse],
    summary="Get user preferences",
)
async def get_preferences(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = await settings_service.get_preferences(db=db, user_id=current_user.id)
    return StandardResponse(success=True, message="Preferences retrieved successfully.", data=data)

@router.patch(
    "/preferences",
    response_model=StandardResponse[UserSettingsResponse],
    summary="Update user preferences",
)
async def update_preferences(
    payload: UserPreferencesUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = await settings_service.update_preferences(db=db, user_id=current_user.id, data=payload)
    return StandardResponse(success=True, message="Preferences updated successfully.", data=data)

@router.get(
    "/account-summary",
    response_model=StandardResponse[AccountSummaryResponse],
    summary="Get account summary",
)
async def get_account_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = await settings_service.get_account_summary(db=db, user=current_user)
    return StandardResponse(success=True, message="Account summary retrieved successfully.", data=data)
