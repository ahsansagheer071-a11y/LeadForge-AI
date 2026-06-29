import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class UserSettingsBase(BaseModel):
    gemini_api_key: Optional[str] = Field(default=None, max_length=255)
    serpapi_key: Optional[str] = Field(default=None, max_length=255)
    cloudinary_cloud_name: Optional[str] = Field(default=None, max_length=100)
    cloudinary_api_key: Optional[str] = Field(default=None, max_length=100)
    cloudinary_api_secret: Optional[str] = Field(default=None, max_length=255)


class UserSettingsCreate(UserSettingsBase):
    pass


class UserSettingsUpdate(BaseModel):
    gemini_api_key: Optional[str] = Field(default=None, max_length=255)
    serpapi_key: Optional[str] = Field(default=None, max_length=255)
    cloudinary_cloud_name: Optional[str] = Field(default=None, max_length=100)
    cloudinary_api_key: Optional[str] = Field(default=None, max_length=100)
    cloudinary_api_secret: Optional[str] = Field(default=None, max_length=255)


class UserSettingsResponse(BaseModel):
    """
    Safe response schema for user settings.
    API keys are never returned in plaintext — boolean flags indicate whether they are set.
    """
    id: uuid.UUID
    user_id: uuid.UUID
    cloudinary_cloud_name: Optional[str] = None
    cloudinary_api_key: Optional[str] = None
    gemini_api_key_set: bool = False
    serpapi_key_set: bool = False
    cloudinary_api_secret_set: bool = False
    
    # Preferences
    theme: str
    email_notifications: bool
    default_page_size: int
    default_sorting: str
    language: str

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_model(cls, obj: object) -> "UserSettingsResponse":
        """
        Build a safe response from a SQLAlchemy UserSettings ORM object.
        Masks sensitive API key values and replaces them with boolean presence flags.
        """
        return cls(
            id=obj.id,
            user_id=obj.user_id,
            cloudinary_cloud_name=obj.cloudinary_cloud_name,
            cloudinary_api_key=obj.cloudinary_api_key,
            gemini_api_key_set=bool(obj.gemini_api_key),
            serpapi_key_set=bool(obj.serpapi_key),
            cloudinary_api_secret_set=bool(obj.cloudinary_api_secret),
            theme=obj.theme,
            email_notifications=obj.email_notifications,
            default_page_size=obj.default_page_size,
            default_sorting=obj.default_sorting,
            language=obj.language,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )

class UserPreferencesUpdate(BaseModel):
    theme: Optional[str] = Field(default=None, max_length=20)
    email_notifications: Optional[bool] = None
    default_page_size: Optional[int] = Field(default=None, ge=1, le=100)
    default_sorting: Optional[str] = Field(default=None, max_length=50)
    language: Optional[str] = Field(default=None, max_length=20)

class AccountSummaryResponse(BaseModel):
    user_info: "UserResponse"
    total_leads: int
    total_audits: int
    total_outreach: int
    account_created_at: datetime

# Handle forward references
from app.schemas.user import UserResponse
AccountSummaryResponse.model_rebuild()
