from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import Optional
from .base import BaseRepository
from ..models import TrainWords


class WordRepository(BaseRepository[TrainWords]):
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, TrainWords)
    
    async def get_by_text(self, word: str) -> Optional[TrainWords]:
        result = await self.db.execute(
            select(TrainWords).where(TrainWords.word == word)
        )
        return result.scalar_one_or_none()

