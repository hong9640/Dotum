"""
BaseRepository - 공통 Repository 베이스 클래스

모든 도메인별 Repository가 상속받아야 하는 제네릭 베이스 클래스
"""
from typing import TypeVar, Generic, Type, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func
from sqlmodel import SQLModel, select

T = TypeVar("T", bound=SQLModel)


class BaseRepository(Generic[T]):
    """
    제네릭 Repository 베이스 클래스
    
    모든 도메인별 Repository는 이 클래스를 상속받아 사용
    기본적인 CRUD 작업을 제공
    
    Usage:
        class UserRepository(BaseRepository[User]):
            def __init__(self, db: AsyncSession):
                super().__init__(db, User)
    """
    
    def __init__(self, db: AsyncSession, model: Type[T]):
        """
        Args:
            db: 데이터베이스 세션
            model: SQLModel 모델 클래스
        """
        self.db = db
        self.model = model
    
    async def get_random(self, limit: int = 1) -> List[T]:
        """랜덤으로 엔티티 조회"""
        result = await self.db.execute(
            select(self.model)
            .order_by(func.random())
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_by_id(self, id: int) -> Optional[T]:
        """ID로 엔티티 조회"""
        return await self.db.get(self.model, id)
    
    async def get_all(self, limit: int = 100) -> List[T]:
        """모든 엔티티 조회 (limit 적용)"""
        result = await self.db.execute(
            select(self.model).limit(limit)
        )
        return result.scalars().all()
    
    async def create(self, entity: T) -> T:
        """엔티티 생성"""
        self.db.add(entity)
        await self.db.commit()
        await self.db.refresh(entity)
        return entity
    
    async def update(self, entity: T) -> T:
        """엔티티 업데이트"""
        await self.db.commit()
        await self.db.refresh(entity)
        return entity
    
    async def delete(self, id: int) -> bool:
        """ID로 엔티티 삭제"""
        entity = await self.db.get(self.model, id)
        if not entity:
            return False
        await self.db.delete(entity)
        await self.db.commit()
        return True

