"""
Dashboard Analytics Endpoints
Registered in main.py under prefix /api/v1/dashboard.

All endpoints:
- Require JWT authentication via get_current_user
- Are fully async
- Return StandardResponse[T] to match the rest of the API
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.response import StandardResponse
from app.schemas.dashboard_schemas import (
    DashboardSummaryResponse,
    DistributionResponse,
    RecentLeadsResponse,
)
from app.services.dashboard_service import dashboard_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/summary",
    response_model=StandardResponse[DashboardSummaryResponse],
    summary="Dashboard KPI Summary",
    description=(
        "Returns high-level KPI counters for the authenticated user's workspace: "
        "total leads, new leads, audited leads, outreach generated, "
        "average lead score, and high-priority leads (score ≥ 90)."
    ),
    responses={
        200: {"description": "KPI summary successfully retrieved"},
        401: {"description": "Missing or invalid JWT token"},
        503: {"description": "Database error"},
    },
)
async def get_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[DashboardSummaryResponse]:
    logger.info("GET /dashboard/summary | user_id=%s", current_user.id)
    data = await dashboard_service.get_summary(db=db, user_id=current_user.id)
    return StandardResponse(success=True, message="Dashboard summary retrieved successfully.", data=data)


@router.get(
    "/recent-leads",
    response_model=StandardResponse[RecentLeadsResponse],
    summary="Recent Leads (paginated)",
    description=(
        "Returns the most recently created leads for the authenticated user, sorted newest-first. "
        "Supports pagination via `limit` (default 10, max 100) and `offset` (default 0)."
    ),
    responses={
        200: {"description": "Recent leads retrieved successfully"},
        401: {"description": "Missing or invalid JWT token"},
    },
)
async def get_recent_leads(
    limit: Optional[int] = Query(default=10, ge=1, le=100, description="Number of leads to return"),
    offset: Optional[int] = Query(default=0, ge=0, description="Number of leads to skip"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[RecentLeadsResponse]:
    logger.info("GET /dashboard/recent-leads | user_id=%s | limit=%s | offset=%s",
                current_user.id, limit, offset)
    data = await dashboard_service.get_recent_leads(
        db=db, user_id=current_user.id, limit=limit, offset=offset
    )
    return StandardResponse(success=True, message="Recent leads retrieved successfully.", data=data)


@router.get(
    "/status-distribution",
    response_model=StandardResponse[DistributionResponse],
    summary="Lead Status Distribution",
    description="Returns lead counts grouped by pipeline status for the authenticated user.",
)
async def get_status_distribution(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[DistributionResponse]:
    logger.info("GET /dashboard/status-distribution | user_id=%s", current_user.id)
    data = await dashboard_service.get_status_distribution(db=db, user_id=current_user.id)
    return StandardResponse(success=True, message="Status distribution retrieved successfully.", data=data)


@router.get(
    "/industry-distribution",
    response_model=StandardResponse[DistributionResponse],
    summary="Lead Industry Distribution",
    description="Returns lead counts grouped by industry for the authenticated user.",
)
async def get_industry_distribution(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[DistributionResponse]:
    logger.info("GET /dashboard/industry-distribution | user_id=%s", current_user.id)
    data = await dashboard_service.get_industry_distribution(db=db, user_id=current_user.id)
    return StandardResponse(success=True, message="Industry distribution retrieved successfully.", data=data)


@router.get(
    "/city-distribution",
    response_model=StandardResponse[DistributionResponse],
    summary="Lead City Distribution",
    description="Returns lead counts grouped by city for the authenticated user.",
)
async def get_city_distribution(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[DistributionResponse]:
    logger.info("GET /dashboard/city-distribution | user_id=%s", current_user.id)
    data = await dashboard_service.get_city_distribution(db=db, user_id=current_user.id)
    return StandardResponse(success=True, message="City distribution retrieved successfully.", data=data)