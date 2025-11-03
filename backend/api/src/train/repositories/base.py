from typing import TypeVar, Generic, Type, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func
from sqlmodel import SQLModel, select

T = TypeVar("T", bound=SQLModel)

class BaseRepository(Generic[T]):
    
    def __init__(self, db: AsyncSession, model: Type[T]):
        self.db = db
        self.model = model
    
    async def get_random(self, limit: int = 1) -> List[T]:
        result = await self.db.execute(
            select(self.model)
            .order_by(func.random())
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_by_id(self, id: int) -> Optional[T]:
        return await self.db.get(self.model, id)
    
    async def get_all(self, limit: int = 100) -> List[T]:
        result = await self.db.execute(
            select(self.model).limit(limit)
        )
        return result.scalars().all()
    
    async def create(self, entity: T) -> T:
        self.db.add(entity)
        await self.db.commit()
        await self.db.refresh(entity)
        return entity
    
    async def update(self, entity: T) -> T:
        await self.db.commit()
        await self.db.refresh(entity)
        return entity
    
    async def delete(self, id: int) -> bool:
        entity = await self.db.get(self.model, id)
        if not entity:
            return False
        await self.db.delete(entity)
        await self.db.commit()
        return True

