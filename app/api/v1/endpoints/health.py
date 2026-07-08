from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.config import settings
from app.database.session import get_db
from app.core.logging import logger

router = APIRouter()


@router.get("", status_code=status.HTTP_200_OK)
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Enhanced health check endpoint to monitor database connectivity,
    AI provider configuration, and overall API health.
    """
    database_status = "healthy"
    status_code = status.HTTP_200_OK

    try:
        # Perform a basic query on the database connection
        await db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        database_status = "unhealthy"
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    # Check configuration status of all AI providers
    groq_status = "configured" if settings.GROQ_API_KEY else "unconfigured"
    pollinations_status = "configured" if settings.POLLINATIONS_API_KEY else "unconfigured"
    nvidia_status = "configured" if settings.NVIDIA_API_KEY else "unconfigured"
    serpapi_status = "configured" if settings.SERPAPI_KEY else "unconfigured"
    cloudinary_status = "configured" if (
        settings.CLOUDINARY_CLOUD_NAME and
        settings.CLOUDINARY_API_KEY and
        settings.CLOUDINARY_API_SECRET
    ) else "unconfigured"

    return {
        "status": "online" if database_status == "healthy" else "degraded",
        "version": "1.0.0",
        "environment": settings.ENV,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": database_status,
        "services": {
            "groq": groq_status,
            "pollinations": pollinations_status,
            "nvidia": nvidia_status,
            "serpapi": serpapi_status,
            "cloudinary": cloudinary_status,
        }
    }
