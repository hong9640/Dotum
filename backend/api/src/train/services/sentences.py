from sqlalchemy.ext.asyncio import AsyncSession
from ..schemas import TrainSentenceCreate, TrainSentenceUpdate
from ..models import TrainSentences
from ..repositories import SentenceRepository
from typing import List, Optional


class SentenceService:
    
    def __init__(self, db: AsyncSession):
        self.repo = SentenceRepository(db)
    
    async def get_random_sentences(self, limit: int = 1) -> List[TrainSentences]:
        return await self.repo.get_random(limit)
    
    async def get_sentence_by_id(self, sentence_id: int) -> Optional[TrainSentences]:
        return await self.repo.get_by_id(sentence_id)
    
    async def create_sentence(self, sentence_data: TrainSentenceCreate) -> TrainSentences:
        # 중복 체크
        existing_sentence = await self.repo.get_by_text(sentence_data.sentence)
        if existing_sentence:
            raise ValueError(f"{sentence_data.sentence}은/는 이미 존재합니다")
        
        new_sentence = TrainSentences(sentence=sentence_data.sentence)
        return await self.repo.create(new_sentence)
    
    async def update_sentence(
        self, 
        sentence_id: int, 
        sentence_data: TrainSentenceUpdate
    ) -> Optional[TrainSentences]:
        sentence = await self.repo.get_by_id(sentence_id)
        if not sentence:
            return None
        
        existing_sentence = await self.repo.get_by_text(sentence_data.sentence)
        if existing_sentence and existing_sentence.id != sentence_id:
            raise ValueError(f"{sentence_data.sentence}은/는 이미 존재합니다")
        
        sentence.sentence = sentence_data.sentence
        return await self.repo.update(sentence)
    
    async def delete_sentence(self, sentence_id: int) -> bool:
        return await self.repo.delete(sentence_id)

