from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.core.config import settings
from app.core.logging import logger

# Create async engine for PostgreSQL
# We configure pool settings for production scalability
async_engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=10,
    echo=settings.DEBUG
)

# Async sessionmaker
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency generator for obtaining async database sessions.
    Automatically commits or rolls back based on exceptions.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            # Auto-commit on successful request execution
            await session.commit()
        except Exception as e:
            logger.error(f"Database session encountered error, rolling back: {str(e)}")
            await session.rollback()
            raise
        finally:
            await session.close()
