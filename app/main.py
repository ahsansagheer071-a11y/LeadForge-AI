import asyncio
import sys

# Fix Playwright subprocess issue on Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(
        asyncio.WindowsProactorEventLoopPolicy()
    )


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.core.logging import logger

from app.middleware.error_handler import register_exception_handlers
from app.middleware.request_id import RequestIDMiddleware

from app.api.v1.endpoints import (
    health,
    auth,
    leads,
    analysis,
    screenshots,
    audits,
    outreach,
    generation,
    dashboard_endpoint
)

from app.api.v1.endpoints import settings as settings_endpoint



app = FastAPI(

    title="LeadForge AI Backend",

    description=(
        "Production-ready AI-powered Lead Intelligence API for digital marketing agencies. "
        "Allows lead discovery, deep website auditing, screenshot capture, automated AI "
        "recommendations, and outreach generation."
    ),

    version="1.0.0",

    docs_url="/docs",

    redoc_url="/redoc",

    openapi_url="/api/v1/openapi.json"
)



origins = [
    o.strip()
    for o in settings.CORS_ORIGINS.split(",")
    if o.strip()
]


app.add_middleware(

    CORSMiddleware,

    allow_origins=origins if origins else ["*"],

    allow_credentials=True if origins else False,

    allow_methods=["*"],

    allow_headers=["*"],
)



app.add_middleware(
    RequestIDMiddleware
)



register_exception_handlers(app)



app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["Authentication"]
)


app.include_router(
    health.router,
    prefix="/health",
    tags=["Health"]
)


app.include_router(
    leads.router,
    prefix="/api/v1/leads",
    tags=["Leads"]
)


app.include_router(
    analysis.router,
    prefix="/api/v1/analysis",
    tags=["Analysis"]
)


app.include_router(
    screenshots.router,
    prefix="/api/v1/screenshots",
    tags=["Screenshots"]
)


app.include_router(
    audits.router,
    prefix="/api/v1/audits",
    tags=["AI Audits & Scoring"]
)


app.include_router(
    outreach.router,
    prefix="/api/v1/outreach",
    tags=["Outreach Generation"]
)


app.include_router(
    generation.router,
    prefix="/api/v1/generation",
    tags=["Website Generation"]
)


app.include_router(
    dashboard_endpoint.router,
    prefix="/api/v1/dashboard",
    tags=["Dashboard Analytics"]
)


app.include_router(
    settings_endpoint.router,
    prefix="/api/v1/settings",
    tags=["Settings & Account Management"]
)




@app.on_event("startup")
async def startup_event():

    logger.info(
        "Starting up LeadForge AI Backend service..."
    )


    logger.info(
        f"Environment: {settings.ENV}"
    )


    logger.info(
        f"Debug Mode: {settings.DEBUG}"
    )



    if not settings.DATABASE_URL:

        logger.critical(
            "DATABASE_URL is not set!"
        )

        raise RuntimeError(
            "DATABASE_URL is not set!"
        )



    if (
        not settings.JWT_SECRET
        or settings.JWT_SECRET == "your_super_secret_jwt_signing_key_here"
    ):

        if settings.ENV == "production":

            raise RuntimeError(
                "Insecure JWT_SECRET configured in production environment!"
            )

        else:

            logger.warning(
                "Using default JWT_SECRET in development."
            )




    from app.database.session import async_engine
    from sqlalchemy import text


    try:

        async with async_engine.connect() as conn:

            await conn.execute(
                text("SELECT 1")
            )


        logger.info(
            "Database connectivity verified successfully."
        )


    except Exception as e:

        logger.critical(
            f"Database connection failed: {str(e)}"
        )

        raise


    if not settings.GROQ_API_KEY:

        logger.warning(
            "GROQ_API_KEY not configured."
        )

    else:

        logger.info(
            "Groq configuration loaded."
        )


    if not settings.SERPAPI_KEY:

        logger.warning(
            "SERPAPI_KEY not configured."
        )

    else:

        logger.info(
            "SerpAPI configuration loaded."
        )




    import os


    try:

        os.makedirs(
            settings.SCREENSHOTS_DIR,
            exist_ok=True
        )


        test_file = os.path.join(
            settings.SCREENSHOTS_DIR,
            ".write_test"
        )


        with open(test_file, "w") as f:

            f.write("test")


        os.remove(test_file)


        logger.info(
            f"Screenshots directory ready: {settings.SCREENSHOTS_DIR}"
        )



    except Exception as e:

        logger.critical(
            f"Screenshots directory failed: {str(e)}"
        )

        raise





@app.on_event("shutdown")
async def shutdown_event():

    logger.info(
        "Shutting down LeadForge AI Backend service..."
    )




@app.get("/", include_in_schema=False)
async def root_redirect():

    return RedirectResponse(
        url="/docs"
    )