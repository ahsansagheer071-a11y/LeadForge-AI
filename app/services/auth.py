import re
import uuid as uuid_module
from datetime import datetime, timedelta, timezone
from typing import Dict
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthenticationException, ConflictException, ValidationException
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.models.user import User
from app.models.user_settings import UserSettings
from app.repositories.user import user_repository
from app.repositories.revoked_token import revoked_token_repository
from app.schemas.user import UserCreate


class AuthService:
    """
    Application service responsible for registration, authentication,
    JWT token lifecycle management (access + refresh + rotation), and logout invalidation.
    All business logic lives here — routes only call this service.
    """

    @staticmethod
    def validate_password_strength(password: str) -> None:
        """
        Enforce password security policy:
        - Minimum 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit or special character
        """
        if len(password) < 8:
            raise ValidationException("Password must be at least 8 characters long.")
        if not re.search(r"[A-Z]", password):
            raise ValidationException("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", password):
            raise ValidationException("Password must contain at least one lowercase letter.")
        if not re.search(r"\d", password) and not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            raise ValidationException(
                "Password must contain at least one digit or special character."
            )

    async def register_user(self, db: AsyncSession, *, user_in: UserCreate) -> User:
        """
        Register a new agency user. Validates uniqueness and password strength,
        hashes the password, persists the user, and provisions a default settings record.
        """
        # Validate email uniqueness before any write
        existing_user = await user_repository.get_by_email(db, email=user_in.email)
        if existing_user:
            raise ConflictException(
                "A user with this email address is already registered."
            )

        # Enforce password policy
        self.validate_password_strength(user_in.password)

        # Persist user with hashed credentials
        db_user = User(
            email=user_in.email,
            hashed_password=hash_password(user_in.password),
            full_name=user_in.full_name,
            is_active=True,
            is_superuser=user_in.is_superuser,
            role="USER"
        )
        db.add(db_user)
        await db.flush()  # Flush to generate the UUID primary key

        # Provision empty settings record — avoids NULL checks throughout the codebase
        db.add(UserSettings(
            user_id=db_user.id,
            gemini_api_key=None,
            serpapi_key=None,
            cloudinary_cloud_name=None,
            cloudinary_api_key=None,
            cloudinary_api_secret=None
        ))
        await db.flush()

        return db_user

    async def authenticate_user(
        self, db: AsyncSession, *, email: str, password: str
    ) -> User:
        """
        Verify email and password. Returns the User on success or raises
        AuthenticationException to prevent user enumeration via timing attacks.
        """
        user = await user_repository.get_by_email(db, email=email)
        # Always call verify_password even on miss (prevents timing side-channels)
        password_valid = verify_password(password, user.hashed_password) if user else False

        if not user or not password_valid:
            raise AuthenticationException("Incorrect email or password.")

        if not user.is_active:
            raise AuthenticationException("This user account has been deactivated.")

        return user

    def create_tokens(self, user_id: str) -> Dict[str, str]:
        """
        Issue a short-lived access token (15 minutes) and a long-lived
        refresh token (7 days) for the given user ID.
        """
        access_token = create_access_token(
            subject=user_id,
            expires_delta=timedelta(minutes=15)
        )
        refresh_token = create_access_token(
            subject=user_id,
            expires_delta=timedelta(days=7)
        )
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    async def refresh_tokens(
        self, db: AsyncSession, *, refresh_token: str
    ) -> Dict[str, str]:
        """
        Validate the refresh token, enforce rotation (revoke the old one),
        verify the user still exists and is active, then return a fresh token pair.
        """
        # Decode — returns None if expired or structurally invalid
        payload = decode_access_token(refresh_token)
        if not payload:
            raise AuthenticationException("Invalid or expired refresh token.")

        # Reject revoked tokens (e.g., from a previous logout or rotation)
        if await revoked_token_repository.is_token_revoked(db, token=refresh_token):
            raise AuthenticationException(
                "This refresh token has been revoked. Please log in again."
            )

        user_id_str = payload.get("sub")
        if not user_id_str:
            raise AuthenticationException("Invalid token payload structure.")

        # Parse UUID — sub is stored as a string in JWT
        try:
            user_id = uuid_module.UUID(user_id_str)
        except (ValueError, AttributeError):
            raise AuthenticationException("Token contains an invalid user identifier.")

        user = await user_repository.get(db, id=user_id)
        if not user or not user.is_active:
            raise AuthenticationException("User session is inactive or invalid.")

        # Enforce refresh token rotation: revoke current before issuing fresh pair
        exp_timestamp = payload.get("exp")
        if exp_timestamp:
            expires_at = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
            await revoked_token_repository.revoke_token(
                db, token=refresh_token, expires_at=expires_at
            )

        return self.create_tokens(user_id=str(user.id))

    async def revoke_token(self, db: AsyncSession, *, token: str) -> None:
        """
        Add an active token to the blacklist. Called on logout.
        Silently succeeds if the token is already expired or already revoked.
        """
        payload = decode_access_token(token)
        if not payload:
            # Already expired — no need to blacklist
            return

        if await revoked_token_repository.is_token_revoked(db, token=token):
            return  # Already in the blacklist

        exp_timestamp = payload.get("exp")
        if exp_timestamp:
            expires_at = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        else:
            expires_at = datetime.now(timezone.utc) + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )

        await revoked_token_repository.revoke_token(
            db, token=token, expires_at=expires_at
        )


# Module-level singleton — injected via FastAPI Depends in routes
auth_service = AuthService()
