from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    """
    Schema for access and refresh tokens returned on successful login or refresh.
    """
    access_token: str = Field(..., description="JWT access token used for accessing protected endpoints")
    refresh_token: str = Field(..., description="JWT refresh token used to obtain a new access token")
    token_type: str = Field(default="bearer", description="Token type, usually Bearer")


class RefreshRequest(BaseModel):
    """
    Schema representing the refresh token validation payload.
    """
    refresh_token: str = Field(..., description="The long-lived refresh token")
