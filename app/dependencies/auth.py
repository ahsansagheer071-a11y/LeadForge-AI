import uuid as uuid_module
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationException, ForbiddenException
from app.core.security import decode_access_token
from app.database.session import get_db
from app.models.user import User
from app.repositories.user import user_repository
from app.repositories.revoked_token import revoked_token_repository

# Defines the scheme to extract token from Authorization: Bearer <token> header
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=True
)


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    Extracts and validates the JWT token from the request Authorization header.
    Returns the authenticated User instance or raises AuthenticationException (HTTP 401).
    """
    # 1. Decode and structurally validate the JWT token
    payload = decode_access_token(token)
    if not payload:
        raise AuthenticationException(
            "Could not validate credentials. Token is invalid or expired."
        )

    # 2. Check the revocation blacklist to support immediate logout invalidation
    is_revoked = await revoked_token_repository.is_token_revoked(db, token=token)
    if is_revoked:
        raise AuthenticationException("Token has been revoked. Please log in again.")

    # 3. Extract user ID from token subject claim
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise AuthenticationException("Token payload structure is invalid.")

    # 4. Parse UUID (JWT sub is stored as string, DB expects UUID type)
    try:
        user_id = uuid_module.UUID(user_id_str)
    except (ValueError, AttributeError):
        raise AuthenticationException("Token contains an invalid user identifier.")

    # 5. Load user from database
    user = await user_repository.get(db, id=user_id)
    if not user:
        raise AuthenticationException("User matching this session does not exist.")

    if not user.is_active:
        raise AuthenticationException("This user account has been deactivated.")

    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency that extends get_current_user to enforce admin-level authorization.
    Raises HTTP 403 Forbidden if the user is not an ADMIN or superuser.
    """
    if current_user.role != "ADMIN" and not current_user.is_superuser:
        raise ForbiddenException(
            "You do not have permission to perform this action. Admin access required."
        )
    return current_user
