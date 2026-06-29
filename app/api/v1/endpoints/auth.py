from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationException, ConflictException, ValidationException
from app.database.session import get_db
from app.dependencies.auth import get_current_user, oauth2_scheme
from app.models.user import User
from app.schemas.response import StandardResponse
from app.schemas.user import UserCreate, UserResponse
from app.schemas.token import TokenResponse, RefreshRequest
from app.services.auth import auth_service

router = APIRouter()


@router.post(
    "/register",
    response_model=StandardResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new agency user",
    description=(
        "Create a new agency owner user account in the LeadForge AI system. "
        "Performs password strength and email uniqueness validation. "
        "Automatically provisions default settings config for the user."
    ),
    responses={
        201: {"description": "User successfully registered and settings provisioned."},
        400: {"description": "Invalid input formatting or validation failure."},
        409: {"description": "A user with this email address already exists."}
    }
)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    user = await auth_service.register_user(db, user_in=user_in)
    return StandardResponse(
        success=True,
        message="User registered successfully.",
        data=UserResponse.model_validate(user)
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Login user and obtain access token",
    description=(
        "Authenticate using OAuth2 compatible email (username) and password form. "
        "Returns short-lived access token (15 mins) and long-lived refresh token (7 days)."
    ),
    responses={
        200: {"description": "Authentication successful, token returned."},
        401: {"description": "Incorrect email or password."}
    }
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    user = await auth_service.authenticate_user(
        db,
        email=form_data.username,
        password=form_data.password
    )
    tokens = auth_service.create_tokens(user_id=str(user.id))
    return TokenResponse(**tokens)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access tokens",
    description=(
        "Obtain a new access and refresh token pair using an unexpired, active refresh token. "
        "Applies Refresh Token Rotation to revoke the previous refresh token."
    ),
    responses={
        200: {"description": "Access token refreshed successfully."},
        401: {"description": "Invalid, expired, or blacklisted refresh token."}
    }
)
async def refresh(
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db)
):
    tokens = await auth_service.refresh_tokens(db, refresh_token=payload.refresh_token)
    return TokenResponse(**tokens)


@router.post(
    "/logout",
    response_model=StandardResponse[None],
    status_code=status.HTTP_200_OK,
    summary="Revoke access session",
    description=(
        "Add the current active access token to the database blacklist, "
        "preventing any subsequent requests until authorization credentials are regenerated."
    ),
    responses={
        200: {"description": "Token successfully revoked and logged out."}
    }
)
async def logout(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    await auth_service.revoke_token(db, token=token)
    return StandardResponse(
        success=True,
        message="Logged out successfully. Token revoked.",
        data=None
    )


@router.get(
    "/me",
    response_model=StandardResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Fetch current user details",
    description="Retrieve account statistics and metadata details for the currently logged in session.",
    responses={
        200: {"description": "User details successfully retrieved."},
        401: {"description": "Missing or invalid session credentials."}
    }
)
async def read_current_user(
    current_user: User = Depends(get_current_user)
):
    return StandardResponse(
        success=True,
        message="Current user profile retrieved successfully.",
        data=UserResponse.model_validate(current_user)
    )
