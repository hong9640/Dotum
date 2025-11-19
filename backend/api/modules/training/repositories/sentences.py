from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import List, Optional
from api.shared.repositories.base import BaseRepository
from ..models import TrainSentences


class SentenceRepository(BaseRepository[TrainSentences]):
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, TrainSentences)
    
    async def get_by_text(self, sentence: str) -> Optional[TrainSentences]:
        result = await self.db.execute(
            select(TrainSentences).where(TrainSentences.sentence == sentence)
        )
        return result.scalar_one_or_none()