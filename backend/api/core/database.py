from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from api.core.config import settings

engine = create_async_engine(settings.DB_URL, echo=True, future=True)

async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncSession:
    """Dependency for getting async database session.

    Yields:
        AsyncSession: Async database session
    """
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()