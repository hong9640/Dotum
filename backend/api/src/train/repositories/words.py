from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import Optional
from .base import BaseRepository
from ..models import TrainWords


class WordRepository(BaseRepository[TrainWords]):
    """단어 전용 Repository"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, TrainWords)
    
    async def get_by_text(self, word: str) -> Optional[TrainWords]:
        """단어 텍스트로 조회 (단어 전용 로직)"""
        result = await self.db.execute(
            select(TrainWords).where(TrainWords.word == word)
        )
        return result.scalar_one_or_none()

