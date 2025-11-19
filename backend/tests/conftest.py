"""
Pytest 설정 및 공통 Fixtures
"""
import pytest
import asyncio
import threading
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlmodel import SQLModel

from api.core.config import settings

# 모든 모델을 import하여 SQLModel.metadata에 등록
from api.modules.user.models.model import User
from api.modules.auth.models.token import RefreshToken
# Training 모델들도 import (relationship 해결을 위해)
from api.modules.training.models.training_session import TrainingSession
from api.modules.training.models.media import MediaFile


# 테스트용 데이터베이스 URL
# ⚠️ 주의: TEST_DB_URL 환경변수가 없으면 테스트를 실행하지 않음 (실제 DB 보호)
import os
TEST_DB_URL = os.getenv("TEST_DB_URL")
if not TEST_DB_URL:
    raise ValueError(
        "TEST_DB_URL 환경변수가 설정되지 않았습니다. "
        "테스트용 별도 DB를 사용하거나, 테스트를 실행하지 마세요. "
        "실제 운영 DB를 사용하면 데이터가 손실될 수 있습니다!"
    )

# 테이블 생성 락 (동시성 문제 방지)
_tables_created_lock = threading.Lock()
_tables_created = False

# 테스트용 엔진 생성
# 동시성 문제를 방지하기 위해:
# - pool_size를 1로 제한하여 순차 실행 보장
# - pool_pre_ping을 True로 설정하여 연결 유효성 검사
# - 각 테스트마다 독립적인 세션 사용
test_engine = create_async_engine(
    TEST_DB_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,  # 연결 유효성 검사 활성화
    pool_size=1,  # 동시성 문제 방지를 위해 1로 제한
    max_overflow=0,  # 오버플로우 비활성화
    pool_recycle=3600,
    pool_timeout=30,
    # 각 연결이 독립적으로 사용되도록 설정
    connect_args={
        "server_settings": {
            "application_name": "pytest"
        },
        "command_timeout": 60,  # 명령 타임아웃 설정
    }
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# pytest-asyncio가 자동으로 이벤트 루프를 관리하도록 함
# event_loop fixture는 pytest-asyncio가 자동으로 제공

@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    테스트용 데이터베이스 세션
    
    각 테스트마다 새로운 세션과 트랜잭션을 생성하고,
    테스트 후 롤백하여 데이터를 정리합니다.
    
    asyncpg의 동시성 문제를 방지하기 위해:
    - 각 테스트마다 독립적인 세션 사용
    - 트랜잭션을 명확하게 관리
    - 세션을 완전히 닫음
    - 테이블 생성 시 락 사용
    """
    global _tables_created
    
    # 테이블 생성 (스레드 안전하게)
    if not _tables_created:
        with _tables_created_lock:
            # 이중 체크 (락 획득 후 다시 확인)
            if not _tables_created:
                async with test_engine.begin() as conn:
                    await conn.run_sync(SQLModel.metadata.create_all, checkfirst=True)
                _tables_created = True
    
    # 새로운 세션 생성 (각 테스트마다 독립적인 세션)
    session = TestSessionLocal()
    trans = None
    try:
        # 트랜잭션 시작
        trans = await session.begin()
        yield session
    except Exception:
        # 에러 발생 시 롤백
        if trans:
            try:
                await trans.rollback()
            except Exception:
                pass  # 이미 롤백되었거나 닫힌 경우 무시
        raise
    finally:
        # 정리 작업: 트랜잭션 롤백 및 세션 닫기
        if trans:
            try:
                # 트랜잭션이 아직 활성화되어 있으면 롤백
                if trans.is_active:
                    await trans.rollback()
            except Exception:
                pass  # 이미 롤백되었거나 닫힌 경우 무시
        
        # 세션 닫기
        try:
            await session.close()
        except Exception:
            pass  # 이미 닫힌 경우 무시


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """테스트용 사용자 생성"""
    from api.modules.user.models.enum import UserRoleEnum
    from api.modules.auth.services.service import hash_password
    
    user = User(
        username="test@example.com",
        password=hash_password("testpassword123"),
        name="테스트 사용자",
        role=UserRoleEnum.USER
    )
    db_session.add(user)
    await db_session.flush()  # commit 대신 flush 사용 (트랜잭션 내에서)
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_admin_user(db_session: AsyncSession) -> User:
    """테스트용 관리자 사용자 생성"""
    from api.modules.user.models.enum import UserRoleEnum
    from api.modules.auth.services.service import hash_password
    
    user = User(
        username="admin@example.com",
        password=hash_password("adminpassword123"),
        name="테스트 관리자",
        role=UserRoleEnum.ADMIN
    )
    db_session.add(user)
    await db_session.flush()  # commit 대신 flush 사용 (트랜잭션 내에서)
    await db_session.refresh(user)
    return user
