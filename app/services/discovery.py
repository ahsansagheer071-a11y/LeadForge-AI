import uuid
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ValidationException
from app.core.logging import logger
from app.models.lead import Lead
from app.models.user import User
from app.repositories.lead import lead_repository
from app.repositories.user_settings import user_settings_repository
from app.schemas.lead import LeadCreate, LeadDiscoveryResponse, LeadResponse
from app.services.serpapi import serpapi_service


class DiscoveryService:
    """
    Orchestrates lead discovery from SerpAPI Google Maps and persistence.
    """

    async def _resolve_serpapi_key(self, db: AsyncSession, user_id: uuid.UUID) -> str:
        """
        Resolve SerpAPI key using per-user settings first, then global config.
        """
        user_settings = await user_settings_repository.get_by_user_id(db, user_id=user_id)
        api_key = None
        if user_settings and user_settings.serpapi_key:
            api_key = user_settings.serpapi_key
        elif settings.SERPAPI_KEY:
            api_key = settings.SERPAPI_KEY

        if not api_key:
            raise ValidationException(
                "SerpAPI key is not configured. Set SERPAPI_KEY in the environment "
                "or add a serpapi_key in user settings."
            )
        return api_key

    async def discover_leads(
        self,
        db: AsyncSession,
        *,
        user: User,
        business_type: str,
        city: str,
        country: str,
    ) -> LeadDiscoveryResponse:
        """
        Search Google Maps via SerpAPI and store new leads for the authenticated user.
        """
        api_key = await self._resolve_serpapi_key(db, user.id)

        logger.info(
            "Lead discovery started | user_id=%s | business_type=%s | city=%s | country=%s",
            user.id,
            business_type,
            city,
            country,
        )

        payload = await serpapi_service.search_google_maps(
            api_key=api_key,
            business_type=business_type,
            city=city,
            country=country,
        )
        raw_results = serpapi_service.extract_local_results(payload)

        created_leads: List[Lead] = []
        skipped_duplicates = 0

        for raw_result in raw_results:
            parsed = serpapi_service.parse_business_result(raw_result)
            if not parsed:
                logger.warning(
                    "Skipped SerpAPI result without a valid business name | user_id=%s",
                    user.id,
                )
                continue

            duplicate = await lead_repository.find_duplicate(
                db,
                user_id=user.id,
                name=parsed["name"],
                city=city,
                country=country,
                maps_url=parsed.get("maps_url"),
                phone=parsed.get("phone"),
            )
            if duplicate:
                skipped_duplicates += 1
                logger.info(
                    "Skipped duplicate lead | user_id=%s | name=%s | existing_lead_id=%s",
                    user.id,
                    parsed["name"],
                    duplicate.id,
                )
                continue

            lead_in = LeadCreate(
                user_id=user.id,
                name=parsed["name"],
                website=parsed.get("website"),
                phone=parsed.get("phone"),
                address=parsed.get("address"),
                rating=parsed.get("rating"),
                reviews_count=parsed.get("reviews_count"),
                maps_url=parsed.get("maps_url"),
                city=city,
                country=country,
                industry=business_type,
                status="SCRAPED",
            )
            created_lead = await lead_repository.create(db, obj_in=lead_in)
            created_leads.append(created_lead)
            logger.info(
                "Lead created from discovery | user_id=%s | lead_id=%s | name=%s",
                user.id,
                created_lead.id,
                created_lead.name,
            )

        logger.info(
            "Lead discovery completed | user_id=%s | total_found=%s | created=%s | skipped_duplicates=%s",
            user.id,
            len(raw_results),
            len(created_leads),
            skipped_duplicates,
        )

        return LeadDiscoveryResponse(
            total_found=len(raw_results),
            created=len(created_leads),
            skipped_duplicates=skipped_duplicates,
            leads=[LeadResponse.model_validate(lead) for lead in created_leads],
        )


discovery_service = DiscoveryService()
