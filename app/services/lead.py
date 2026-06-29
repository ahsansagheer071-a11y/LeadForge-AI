import csv
import io
import uuid
from typing import List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ValidationException
from app.core.logging import logger
from app.models.lead import Lead
from app.models.user import User
from app.repositories.lead import lead_repository
from app.schemas.lead import (
    BulkActionResponse,
    BulkDeleteRequest,
    BulkStatusUpdateRequest,
    LeadResponse,
    LeadDetailResponse,
    LeadUpdate,
)


class LeadService:
    """
    Orchestrates lead management operations: CRUD, bulk actions, and CSV export.
    """

    async def get_lead(self, db: AsyncSession, lead_id: uuid.UUID, user: User) -> LeadDetailResponse:
        lead = await lead_repository.get_lead_details(db, lead_id)
        if not lead or lead.user_id != user.id:
            raise NotFoundException(f"Lead with id {lead_id} not found.")
        return LeadDetailResponse.model_validate(lead)

    async def update_lead(
        self, db: AsyncSession, lead_id: uuid.UUID, user: User, update_data: LeadUpdate
    ) -> LeadResponse:
        lead = await lead_repository.get(db, lead_id)
        if not lead or lead.user_id != user.id:
            raise NotFoundException(f"Lead with id {lead_id} not found.")

        updated_lead = await lead_repository.update(db, db_obj=lead, obj_in=update_data)
        logger.info("Lead updated | lead_id=%s | user_id=%s", lead_id, user.id)
        return LeadResponse.model_validate(updated_lead)

    async def delete_lead(self, db: AsyncSession, lead_id: uuid.UUID, user: User) -> None:
        lead = await lead_repository.get(db, lead_id)
        if not lead or lead.user_id != user.id:
            raise NotFoundException(f"Lead with id {lead_id} not found.")

        await lead_repository.remove(db, id=lead_id)
        logger.info("Lead deleted | lead_id=%s | user_id=%s", lead_id, user.id)

    async def bulk_delete(
        self, db: AsyncSession, user: User, payload: BulkDeleteRequest
    ) -> BulkActionResponse:
        processed, valid_ids = await lead_repository.bulk_delete(
            db, user_id=user.id, lead_ids=payload.lead_ids
        )
        not_found = len(payload.lead_ids) - processed
        
        logger.info(
            "Bulk delete | user_id=%s | requested=%d | processed=%d",
            user.id, len(payload.lead_ids), processed
        )
        return BulkActionResponse(
            processed=processed, not_found=not_found, lead_ids=valid_ids
        )

    async def bulk_update_status(
        self, db: AsyncSession, user: User, payload: BulkStatusUpdateRequest
    ) -> BulkActionResponse:
        processed, valid_ids = await lead_repository.bulk_update_status(
            db, user_id=user.id, lead_ids=payload.lead_ids, status=payload.status
        )
        not_found = len(payload.lead_ids) - processed
        
        logger.info(
            "Bulk status update | user_id=%s | requested=%d | processed=%d | status=%s",
            user.id, len(payload.lead_ids), processed, payload.status
        )
        return BulkActionResponse(
            processed=processed, not_found=not_found, lead_ids=valid_ids
        )

    async def export_leads_csv(
        self,
        db: AsyncSession,
        user: User,
        name: Optional[str] = None,
        city: Optional[str] = None,
        country: Optional[str] = None,
        status: Optional[str] = None,
        category: Optional[str] = None,
        min_score: Optional[int] = None,
        max_score: Optional[int] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> str:
        """
        Exports filtered leads to CSV string. Limits to 1000 for safety.
        """
        leads, _ = await lead_repository.get_leads_paginated(
            db,
            user_id=user.id,
            page=1,
            limit=1000,
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

        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow([
            "ID", "Name", "Industry", "City", "Country", 
            "Status", "Rating", "Reviews", "Website", "Phone"
        ])
        
        for lead in leads:
            writer.writerow([
                str(lead.id),
                lead.name,
                lead.industry,
                lead.city,
                lead.country,
                lead.status,
                lead.rating or "",
                lead.reviews_count or "",
                lead.website or "",
                lead.phone or ""
            ])
            
        logger.info("CSV Export | user_id=%s | count=%d", user.id, len(leads))
        return output.getvalue()


lead_service = LeadService()
