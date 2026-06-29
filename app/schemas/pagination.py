from typing import Generic, List, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Standard pagination envelope for lists of resources.
    """
    items: List[T]
    total: int = Field(..., description="Total number of items matching the query")
    page: int = Field(..., description="Current page number (1-indexed)")
    limit: int = Field(..., description="Number of items returned per page")
    pages: int = Field(..., description="Total number of pages available")
