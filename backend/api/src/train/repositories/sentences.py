from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import List, Optional
from .base import BaseRepository
from ..models import TrainSentences


class SentenceRepository(BaseRepository[TrainSentences]):
    """문장 전용 Repository"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, TrainSentences)
    
    async def get_by_word_id(self, word_id: int, limit: int = 10) -> List[TrainSentences]:
        """특정 단어 ID에 속한 문장들 조회"""
        result = await self.db.execute(
            select(TrainSentences)
            .limit(limit)
        )
        return result.scalars().all()
