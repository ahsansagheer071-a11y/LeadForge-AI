from typing import Any, Dict, Optional
from fastapi import status


class BaseAppException(Exception):
    """
    Base exception class for all LeadForge AI application errors.
    """
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: Optional[Any] = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.detail = detail


class NotFoundException(BaseAppException):
    """
    Raised when a requested resource is not found in the database.
    """
    def __init__(self, message: str = "Resource not found", detail: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )


class AuthenticationException(BaseAppException):
    """
    Raised during login, registration, or JWT token authentication failures.
    """
    def __init__(self, message: str = "Invalid credentials", detail: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail
        )


class ForbiddenException(BaseAppException):
    """
    Raised when a user doesn't have permissions for an action or resource.
    """
    def __init__(self, message: str = "Permission denied", detail: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class ConflictException(BaseAppException):
    """
    Raised when a constraint or conflict occurs (e.g. user already exists).
    """
    def __init__(self, message: str = "Resource conflict occurred", detail: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )


class ValidationException(BaseAppException):
    """
    Raised when user input validation fails.
    """
    def __init__(self, message: str = "Validation failed", detail: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )


class ServiceUnavailableException(BaseAppException):
    """
    Raised when third-party services (SerpAPI, Gemini, Cloudinary) fail.
    """
    def __init__(self, message: str = "Third-party service unavailable", detail: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail
        )
