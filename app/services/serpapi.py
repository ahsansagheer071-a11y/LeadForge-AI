from typing import Any, Dict, List, Optional

import httpx

from app.core.exceptions import ServiceUnavailableException
from app.core.logging import logger

SERPAPI_BASE_URL = "https://serpapi.com/search.json"
DEFAULT_TIMEOUT_SECONDS = 30.0


class SerpAPIService:
    """
    Async HTTP client for SerpAPI Google Maps searches.
    """

    async def search_google_maps(
        self,
        *,
        api_key: str,
        business_type: str,
        city: str,
        country: str,
        start: int = 0,
    ) -> Dict[str, Any]:
        """
        Search Google Maps businesses via SerpAPI using business type and location.
        """
        query = f"{business_type} {city}, {country}"
        params = {
            "engine": "google_maps",
            "type": "search",
            "q": query,
            "location": f"{city}, {country}",
            "z": 14,
            "api_key": api_key,
            "start": start,
        }

        logger.info(
            "SerpAPI Google Maps search initiated | query=%s | start=%s",
            query,
            start,
        )

        try:
            async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT_SECONDS) as client:
                response = await client.get(SERPAPI_BASE_URL, params=params)
                response.raise_for_status()
                payload = response.json()
        except httpx.TimeoutException as exc:
            logger.error("SerpAPI request timed out | query=%s", query)
            raise ServiceUnavailableException(
                "SerpAPI request timed out. Please try again later.",
                detail={"query": query},
            ) from exc
        except httpx.HTTPStatusError as exc:
            resp_body = ""
            try:
                resp_body = exc.response.text[:500]
            except Exception:
                pass
            logger.error(
                "SerpAPI HTTP error | status=%s | query=%s | body=%s",
                exc.response.status_code,
                query,
                resp_body,
            )
            raise ServiceUnavailableException(
                "SerpAPI returned an error response.",
                detail={
                    "status_code": exc.response.status_code,
                    "query": query,
                },
            ) from exc
        except httpx.RequestError as exc:
            logger.error("SerpAPI request failed | query=%s | error=%s", query, str(exc))
            raise ServiceUnavailableException(
                "Unable to reach SerpAPI. Please try again later.",
                detail={"query": query},
            ) from exc

        if payload.get("error"):
            error_message = payload["error"]
            logger.error("SerpAPI search error | query=%s | error=%s", query, error_message)
            raise ServiceUnavailableException(
                f"SerpAPI search failed: {error_message}",
                detail={"query": query},
            )

        local_results = payload.get("local_results") or []
        logger.info(
            "SerpAPI Google Maps search completed | query=%s | results=%s",
            query,
            len(local_results),
        )
        return payload

    @staticmethod
    def extract_local_results(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract local business results from a SerpAPI Google Maps response.
        """
        local_results = payload.get("local_results")
        if isinstance(local_results, list):
            return local_results
        return []

    @staticmethod
    def parse_business_result(result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Normalize a SerpAPI local result into lead discovery fields.
        """
        name = (result.get("title") or "").strip()
        if not name:
            return None

        place_id = result.get("place_id")
        maps_url = SerpAPIService.build_maps_url(result)

        return {
            "name": name,
            "website": result.get("website"),
            "phone": result.get("phone"),
            "address": result.get("address"),
            "rating": result.get("rating"),
            "reviews_count": result.get("reviews"),
            "maps_url": maps_url,
            "place_id": place_id,
        }

    @staticmethod
    def build_maps_url(result: Dict[str, Any]) -> Optional[str]:
        """
        Build a Google Maps URL from SerpAPI result metadata when available.
        """
        links = result.get("links")
        if isinstance(links, dict):
            for key in ("website", "directions", "share", "place"):
                link = links.get(key)
                if isinstance(link, str) and "google.com/maps" in link:
                    return link

        place_id = result.get("place_id")
        if place_id:
            return f"https://www.google.com/maps/place/?q=place_id:{place_id}"

        gps = result.get("gps_coordinates") or {}
        latitude = gps.get("latitude")
        longitude = gps.get("longitude")
        title = result.get("title")
        if latitude is not None and longitude is not None and title:
            from urllib.parse import quote_plus

            return (
                f"https://www.google.com/maps/search/"
                f"{quote_plus(title)}/@{latitude},{longitude},17z"
            )

        return None


serpapi_service = SerpAPIService()
