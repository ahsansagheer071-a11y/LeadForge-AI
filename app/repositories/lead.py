import uuid
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from app.models.lead import Lead
from app.models.lead_score import LeadScore
from app.schemas.lead import LeadCreate, LeadUpdate
from app.repositories.base import BaseRepository


class LeadRepository(BaseRepository[Lead, LeadCreate, LeadUpdate]):
    """
    Repository for Lead operations, featuring optimized paginated search,
    filters, sorting, and eager loaded relationships to avoid N+1 queries.
    """

    def __init__(self):
        super().__init__(Lead)

    async def get_lead_details(self, db: AsyncSession, lead_id: uuid.UUID) -> Optional[Lead]:
        """
        Fetch a single lead with all its relationships eager loaded.
        """
        query = (
            select(self.model)
            .options(
                joinedload(self.model.score),
                joinedload(self.model.audit),
                joinedload(self.model.screenshot),
                joinedload(self.model.outreach)
            )
            .filter(self.model.id == lead_id)
        )
        result = await db.execute(query)
        return result.scalars().unique().first()

    async def get_leads_paginated(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        page: int = 1,
        limit: int = 10,
        name: Optional[str] = None,
        city: Optional[str] = None,
        country: Optional[str] = None,
        status: Optional[str] = None,
        category: Optional[str] = None,
        min_score: Optional[int] = None,
        max_score: Optional[int] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Tuple[List[Lead], int]:
        """
        Fetch filtered, sorted, and paginated leads list for a user.
        Avoids N+1 query problem by eager loading relationships using joinedload.
        """
        # Determine if we need to join LeadScore for filtering or sorting
        needs_score_join = (
            category is not None 
            or min_score is not None 
            or max_score is not None 
            or sort_by == "score"
        )

        # Build base filter conditions
        conditions = [self.model.user_id == user_id]
        
        if name:
            conditions.append(self.model.name.ilike(f"%{name}%"))
        if city:
            conditions.append(self.model.city.ilike(f"%{city}%"))
        if country:
            conditions.append(self.model.country.ilike(f"%{country}%"))
        if status:
            conditions.append(self.model.status == status)

        # Build count query
        count_query = select(func.count()).select_from(self.model)
        if needs_score_join:
            count_query = count_query.join(self.model.score)
            if category:
                conditions.append(LeadScore.category == category)
            if min_score is not None:
                conditions.append(LeadScore.overall_score >= min_score)
            if max_score is not None:
                conditions.append(LeadScore.overall_score <= max_score)
        
        count_query = count_query.where(*conditions)
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Build core select query
        query = select(self.model).where(*conditions)
        
        if needs_score_join:
            # If not already joined, join here
            query = query.join(self.model.score)
            
        # Eager load related schemas
        query = query.options(
            joinedload(self.model.score),
            joinedload(self.model.audit),
            joinedload(self.model.screenshot),
            joinedload(self.model.outreach)
        )

        # Sort columns configuration
        sort_column = self.model.created_at
        if sort_by == "score":
            sort_column = LeadScore.overall_score
        elif sort_by == "name":
            sort_column = self.model.name
        elif sort_by == "rating":
            sort_column = self.model.rating
        elif sort_by == "created_at":
            sort_column = self.model.created_at

        # Apply ordering direction
        if sort_order.lower() == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        # Offset and pagination limit application
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        result = await db.execute(query)
        items = list(result.scalars().unique().all())

        return items, total

    async def find_duplicate(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        name: str,
        city: str,
        country: str,
        maps_url: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> Optional[Lead]:
        """
        Find an existing lead for the user to prevent duplicate business records.
        """
        normalized_name = name.strip().lower()

        if maps_url:
            query = select(self.model).where(
                self.model.user_id == user_id,
                self.model.maps_url == maps_url,
            )
            result = await db.execute(query)
            duplicate = result.scalars().first()
            if duplicate:
                return duplicate

        if phone:
            query = select(self.model).where(
                self.model.user_id == user_id,
                func.lower(self.model.name) == normalized_name,
                self.model.phone == phone,
            )
            result = await db.execute(query)
            duplicate = result.scalars().first()
            if duplicate:
                return duplicate

        query = select(self.model).where(
            self.model.user_id == user_id,
            func.lower(self.model.name) == normalized_name,
            func.lower(self.model.city) == city.strip().lower(),
            func.lower(self.model.country) == country.strip().lower(),
        )
        result = await db.execute(query)
        return result.scalars().first()

    async def get_dashboard_summary(self, db: AsyncSession, user_id: uuid.UUID) -> dict:
        """
        Generate summary stats for user's dashboard.
        """
        # Count queries
        total_q = select(func.count(self.model.id)).where(self.model.user_id == user_id)
        new_q = select(func.count(self.model.id)).where(self.model.user_id == user_id, self.model.status == "NEW")
        audited_q = select(func.count(self.model.id)).where(self.model.user_id == user_id, self.model.status.in_(["ANALYZED", "OUTREACH_READY"]))
        
        # Joined counts/averages
        outreach_q = select(func.count(self.model.id)).join(self.model.outreach).where(self.model.user_id == user_id)
        avg_score_q = select(func.coalesce(func.avg(LeadScore.overall_score), 0)).join(self.model.score).where(self.model.user_id == user_id)
        high_priority_q = select(func.count(self.model.id)).join(self.model.score).where(self.model.user_id == user_id, LeadScore.overall_score >= 90)

        total = (await db.execute(total_q)).scalar() or 0
        new_leads = (await db.execute(new_q)).scalar() or 0
        audited = (await db.execute(audited_q)).scalar() or 0
        outreach = (await db.execute(outreach_q)).scalar() or 0
        avg_score = float((await db.execute(avg_score_q)).scalar() or 0)
        high_priority = (await db.execute(high_priority_q)).scalar() or 0

        return {
            "total_leads": total,
            "new_leads": new_leads,
            "audited_leads": audited,
            "outreach_generated": outreach,
            "average_lead_score": round(avg_score, 2),
            "high_priority_leads": high_priority
        }

    async def get_status_distribution(self, db: AsyncSession, user_id: uuid.UUID) -> List[dict]:
        """
        Distribution of leads by status.
        """
        query = (
            select(self.model.status, func.count(self.model.id))
            .where(self.model.user_id == user_id)
            .group_by(self.model.status)
        )
        result = await db.execute(query)
        return [{"status": row[0], "count": row[1]} for row in result.all()]

    async def get_industry_distribution(self, db: AsyncSession, user_id: uuid.UUID) -> List[dict]:
        """
        Distribution of leads by industry.
        """
        query = (
            select(self.model.industry, func.count(self.model.id))
            .where(self.model.user_id == user_id)
            .group_by(self.model.industry)
            .order_by(func.count(self.model.id).desc())
        )
        result = await db.execute(query)
        return [{"industry": row[0], "count": row[1]} for row in result.all()]

    async def get_city_distribution(self, db: AsyncSession, user_id: uuid.UUID) -> List[dict]:
        """
        Distribution of leads by city.
        """
        query = (
            select(self.model.city, func.count(self.model.id))
            .where(self.model.user_id == user_id)
            .group_by(self.model.city)
            .order_by(func.count(self.model.id).desc())
        )
        result = await db.execute(query)
        return [{"city": row[0], "count": row[1]} for row in result.all()]

    async def get_recent_leads_for_dashboard(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        limit: int = 10,
        offset: int = 0,
    ):
        """
        Returns (total_count, list_of_dicts) for the dashboard recent-leads panel.
        Scoped to the requesting user. Sorted newest-first.
        Returns plain dicts (not ORM instances) to decouple from SQLAlchemy.
        """
        from sqlalchemy import select, func

        # Count query
        count_q = select(func.count(self.model.id)).where(self.model.user_id == user_id)
        total = (await db.execute(count_q)).scalar() or 0

        # Page slice — only select columns needed by RecentLeadItem
        page_q = (
            select(
                self.model.id,
                self.model.name,
                self.model.industry,
                self.model.city,
                self.model.country,
                self.model.status,
                self.model.rating,
                self.model.created_at,
            )
            .where(self.model.user_id == user_id)
            .order_by(self.model.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(page_q)
        rows = result.all()

        leads = [
            {
                "id": r.id,
                "name": r.name,
                "industry": r.industry,
                "city": r.city,
                "country": r.country,
                "status": r.status,
                "rating": float(r.rating) if r.rating is not None else None,
                "created_at": r.created_at,
            }
            for r in rows
        ]
        return total, leads

    async def bulk_delete(self, db: AsyncSession, *, user_id: uuid.UUID, lead_ids: List[uuid.UUID]) -> Tuple[int, List[uuid.UUID]]:
        """
        Bulk delete leads owned by the user.
        Returns (number of deleted records, list of successfully deleted lead IDs).
        """
        from sqlalchemy import delete
        
        # Verify ownership and get valid IDs
        query = select(self.model.id).where(self.model.user_id == user_id, self.model.id.in_(lead_ids))
        result = await db.execute(query)
        valid_ids = result.scalars().all()
        
        if not valid_ids:
            return 0, []
            
        stmt = delete(self.model).where(self.model.id.in_(valid_ids))
        await db.execute(stmt)
        await db.flush()
        
        return len(valid_ids), list(valid_ids)
        
    async def bulk_update_status(self, db: AsyncSession, *, user_id: uuid.UUID, lead_ids: List[uuid.UUID], status: str) -> Tuple[int, List[uuid.UUID]]:
        """
        Bulk update status of leads owned by the user.
        Returns (number of updated records, list of successfully updated lead IDs).
        """
        from sqlalchemy import update
        
        # Verify ownership and get valid IDs
        query = select(self.model.id).where(self.model.user_id == user_id, self.model.id.in_(lead_ids))
        result = await db.execute(query)
        valid_ids = result.scalars().all()
        
        if not valid_ids:
            return 0, []
            
        stmt = update(self.model).where(self.model.id.in_(valid_ids)).values(status=status)
        await db.execute(stmt)
        await db.flush()
        
        return len(valid_ids), list(valid_ids)
# Instantiated lead repository instance
lead_repository = LeadRepository()
