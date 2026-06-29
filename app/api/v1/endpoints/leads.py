from fastapi import APIRouter, Depends, Query, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from typing import Optional

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.lead import (
    LeadDiscoveryRequest, 
    LeadDiscoveryResponse,
    LeadResponse,
    LeadDetailResponse,
    LeadUpdate,
    BulkActionResponse,
    BulkDeleteRequest,
    BulkStatusUpdateRequest
)
from app.schemas.response import StandardResponse
from app.schemas.pagination import PaginatedResponse
from app.services.discovery import discovery_service
from app.services.lead import lead_service
from app.repositories.lead import lead_repository

router = APIRouter()


@router.post(
    "/discover",
    response_model=StandardResponse[LeadDiscoveryResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Discover leads using SerpAPI Google Maps",
    description=(
        "Search Google Maps for businesses by business type, city, and country. "
        "Parses and stores business details while skipping duplicate records."
    ),
    responses={
        201: {"description": "Lead discovery completed successfully."},
        401: {"description": "Missing or invalid session credentials."},
        422: {"description": "Invalid request body or missing SerpAPI configuration."},
        503: {"description": "SerpAPI service is unavailable or returned an error."},
    },
)
async def discover_leads(
    payload: LeadDiscoveryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await discovery_service.discover_leads(
        db,
        user=current_user,
        business_type=payload.business_type,
        city=payload.city,
        country=payload.country,
    )

    return StandardResponse(
        success=True,
        message=(
            f"Lead discovery completed. Created {result.created} lead(s), "
            f"skipped {result.skipped_duplicates} duplicate(s)."
        ),
        data=result,
    )

@router.get(
    "",
    response_model=StandardResponse[PaginatedResponse[LeadResponse]],
    summary="List leads with advanced search, filtering, and sorting",
)
async def get_leads(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    name: Optional[str] = None,
    city: Optional[str] = None,
    country: Optional[str] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    min_score: Optional[int] = None,
    max_score: Optional[int] = None,
    sort_by: str = Query("created_at", description="Sort by: created_at, name, rating, score"),
    sort_order: str = Query("desc", description="Sort order: asc, desc"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items, total = await lead_repository.get_leads_paginated(
        db,
        user_id=current_user.id,
        page=page,
        limit=limit,
        name=name,
        city=city,
        country=country,
        status=status,
        category=category,
        min_score=min_score,
        max_score=max_score,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    
    pages = (total + limit - 1) // limit
    
    return StandardResponse(
        success=True,
        message="Leads retrieved successfully.",
        data=PaginatedResponse(
            items=[LeadResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            limit=limit,
            pages=pages
        )
    )

@router.get(
    "/export/csv",
    summary="Export leads to CSV",
    response_class=Response,
    responses={
        200: {
            "content": {"text/csv": {}},
            "description": "Returns a CSV file containing the leads.",
        }
    }
)
async def export_leads_csv(
    name: Optional[str] = None,
    city: Optional[str] = None,
    country: Optional[str] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    min_score: Optional[int] = None,
    max_score: Optional[int] = None,
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    csv_data = await lead_service.export_leads_csv(
        db, user=current_user, name=name, city=city, country=country,
        status=status, category=category, min_score=min_score, max_score=max_score,
        sort_by=sort_by, sort_order=sort_order
    )
    
    return Response(
        content=csv_data, 
        media_type="text/csv", 
        headers={"Content-Disposition": "attachment; filename=leads_export.csv"}
    )

@router.post(
    "/bulk-delete",
    response_model=StandardResponse[BulkActionResponse],
    summary="Bulk delete leads",
)
async def bulk_delete_leads(
    payload: BulkDeleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await lead_service.bulk_delete(db, user=current_user, payload=payload)
    return StandardResponse(
        success=True,
        message=f"Successfully deleted {result.processed} lead(s).",
        data=result
    )

@router.patch(
    "/bulk-status",
    response_model=StandardResponse[BulkActionResponse],
    summary="Bulk update lead status",
)
async def bulk_update_lead_status(
    payload: BulkStatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await lead_service.bulk_update_status(db, user=current_user, payload=payload)
    return StandardResponse(
        success=True,
        message=f"Successfully updated status for {result.processed} lead(s).",
        data=result
    )

@router.get(
    "/{lead_id}",
    response_model=StandardResponse[LeadDetailResponse],
    summary="Get single lead details",
)
async def get_lead(
    lead_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await lead_service.get_lead(db, lead_id=lead_id, user=current_user)
    return StandardResponse(
        success=True,
        message="Lead details retrieved successfully.",
        data=result
    )

@router.patch(
    "/{lead_id}",
    response_model=StandardResponse[LeadResponse],
    summary="Update single lead",
)
async def update_lead(
    lead_id: uuid.UUID,
    payload: LeadUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await lead_service.update_lead(db, lead_id=lead_id, user=current_user, update_data=payload)
    return StandardResponse(
        success=True,
        message="Lead updated successfully.",
        data=result
    )

@router.delete(
    "/{lead_id}",
    response_model=StandardResponse[None],
    summary="Delete single lead",
)
async def delete_lead(
    lead_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await lead_service.delete_lead(db, lead_id=lead_id, user=current_user)
    return StandardResponse(
        success=True,
        message="Lead deleted successfully.",
        data=None
    )
