from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import List, Optional
from .base import BaseRepository
from ..models import WordTrainResults, SentenceTrainResults


class WordTrainResultRepository(BaseRepository[WordTrainResults]):
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, WordTrainResults)
    
    async def get_by_user_id(self, user_id: int, limit: int = 100) -> List[WordTrainResults]:
        result = await self.db.execute(
            select(WordTrainResults)
            .where(WordTrainResults.user_id == user_id)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_by_word_id(self, word_id: int, limit: int = 100) -> List[WordTrainResults]:
        result = await self.db.execute(
            select(WordTrainResults)
            .where(WordTrainResults.train_words_id == word_id)
            .limit(limit)
        )
        return result.scalars().all()


class SentenceTrainResultRepository(BaseRepository[SentenceTrainResults]):
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, SentenceTrainResults)
    
    async def get_by_user_id(self, user_id: int, limit: int = 100) -> List[SentenceTrainResults]:
        result = await self.db.execute(
            select(SentenceTrainResults)
            .where(SentenceTrainResults.user_id == user_id)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_by_sentence_id(self, sentence_id: int, limit: int = 100) -> List[SentenceTrainResults]:
        result = await self.db.execute(
            select(SentenceTrainResults)
            .where(SentenceTrainResults.train_sentences_id == sentence_id)
            .limit(limit)
        )
        return result.scalars().all()

