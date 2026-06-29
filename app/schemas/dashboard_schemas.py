"""
Dashboard Analytics Schemas
Pydantic models aligned with the existing LeadForge AI architecture.
- Lead.id is uuid.UUID (not int)
- Lead.name (not business_name)
- StandardResponse wrapper used throughout the project
- model_config = ConfigDict(...) pattern
"""
import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

class DashboardSummaryResponse(BaseModel):
    """Aggregated KPI card data returned by GET /dashboard/summary."""

    total_leads: int = Field(..., description="Total number of leads owned by this user")
    new_leads: int = Field(..., description="Leads with status NEW")
    audited_leads: int = Field(..., description="Leads with status ANALYZED or OUTREACH_READY")
    outreach_generated: int = Field(..., description="Leads that have outreach content generated")
    average_lead_score: float = Field(..., description="Mean overall_score across all scored leads (0 if none)")
    high_priority_leads: int = Field(..., description="Leads whose overall_score >= 90")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_leads": 342,
                "new_leads": 58,
                "audited_leads": 120,
                "outreach_generated": 89,
                "average_lead_score": 71.4,
                "high_priority_leads": 47,
            }
        }
    )


# ---------------------------------------------------------------------------
# Recent Leads
# ---------------------------------------------------------------------------

class RecentLeadItem(BaseModel):
    """Minimal lead projection used in the recent-leads list."""

    id: uuid.UUID = Field(..., description="Lead primary key (UUID)")
    name: str = Field(..., description="Business name")
    industry: str = Field(..., description="Industry / niche")
    city: str = Field(..., description="City of the business")
    country: str = Field(..., description="Country of the business")
    status: str = Field(..., description="Current lead pipeline status")
    rating: Optional[float] = Field(None, description="Google Maps rating")
    created_at: datetime = Field(..., description="Timestamp when the lead was created")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "name": "Alpha Digital",
                "industry": "Marketing",
                "city": "Karachi",
                "country": "Pakistan",
                "status": "ANALYZED",
                "rating": 4.5,
                "created_at": "2025-06-01T09:30:00Z",
            }
        },
    )


class RecentLeadsResponse(BaseModel):
    """Paginated wrapper for recent-leads list."""

    total: int = Field(..., description="Total leads in this user's workspace")
    limit: int = Field(..., description="Page size used")
    offset: int = Field(..., description="Offset used")
    leads: List[RecentLeadItem] = Field(..., description="Leads for this page")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 342,
                "limit": 10,
                "offset": 0,
                "leads": [
                    {
                        "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                        "name": "Alpha Digital",
                        "industry": "Marketing",
                        "city": "Karachi",
                        "country": "Pakistan",
                        "status": "ANALYZED",
                        "rating": 4.5,
                        "created_at": "2025-06-01T09:30:00Z",
                    }
                ],
            }
        }
    )


# ---------------------------------------------------------------------------
# Distribution helpers
# ---------------------------------------------------------------------------

class DistributionItem(BaseModel):
    """Generic key → count bucket used by all distribution endpoints."""

    label: str = Field(..., description="Group label (status / industry / city)")
    count: int = Field(..., description="Number of leads in this group")

    model_config = ConfigDict(
        json_schema_extra={"example": {"label": "ANALYZED", "count": 120}}
    )


class DistributionResponse(BaseModel):
    """Wrapper that includes total for quick percentage calculations."""

    total: int = Field(..., description="Sum of all counts")
    distribution: List[DistributionItem] = Field(
        ..., description="Sorted distribution buckets (descending count)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 342,
                "distribution": [
                    {"label": "NEW", "count": 120},
                    {"label": "ANALYZED", "count": 89},
                    {"label": "OUTREACH_READY", "count": 58},
                ],
            }
        }
    )
