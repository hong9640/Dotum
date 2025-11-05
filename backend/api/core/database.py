from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from api.core.config import settings

# 성능 최적화된 데이터베이스 엔진 설정
engine = create_async_engine(
    settings.DB_URL,
    # SQL 쿼리 로깅 (DEBUG 모드에서만 활성화)
    echo=settings.DB_ECHO or settings.DEBUG,
    future=True,
    
    # 커넥션 풀 최적화
    pool_size=settings.DB_POOL_SIZE,  # 기본 유지 연결 수
    max_overflow=settings.DB_MAX_OVERFLOW,  # 추가 생성 가능한 연결 수
    pool_recycle=settings.DB_POOL_RECYCLE,  # 커넥션 재활용 시간 (초)
    pool_pre_ping=settings.DB_POOL_PRE_PING,  # 커넥션 사용 전 유효성 검사
    
    # 추가 최적화 옵션
    pool_timeout=30,  # 커넥션을 얻기 위한 최대 대기 시간 (초)
)

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