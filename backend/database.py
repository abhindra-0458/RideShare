from sqlalchemy import create_engine, pool
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from config import settings
import logging

logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    """Base class for all models"""
    pass

# For async operations
async_engine = create_async_engine(
    settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.environment == "development",
    future=True,
    pool_size=20,
    max_overflow=40,
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    """Get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            await session.close()

# Synchronous engine for migrations
sync_engine = create_engine(
    settings.database_url,
    echo=settings.environment == "development",
    poolclass=pool.QueuePool,
    pool_size=20,
    max_overflow=40,
)
