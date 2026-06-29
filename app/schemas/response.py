from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class StandardResponse(BaseModel, Generic[T]):
    """
    Consistent response wrapper for all API success responses.
    """
    success: bool = Field(default=True, description="Indicates whether the request was successful")
    message: str = Field(..., description="A friendly human-readable message detailing the outcome")
    data: Optional[T] = Field(default=None, description="The returned data payload")
