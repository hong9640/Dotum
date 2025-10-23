from sqlalchemy.ext.asyncio import AsyncSession
from ..schemas import (
    WordTrainResultCreate,
    WordTrainResultUpdate,
    SentenceTrainResultCreate,
    SentenceTrainResultUpdate,
)
from ..models import WordTrainResults, SentenceTrainResults
from ..repositories import WordTrainResultRepository, SentenceTrainResultRepository
from typing import List, Optional


class WordTrainResultService:
    
    def __init__(self, db: AsyncSession):
        self.repo = WordTrainResultRepository(db)
    
    async def get_result_by_id(self, result_id: int) -> Optional[WordTrainResults]:
        return await self.repo.get_by_id(result_id)
    
    async def get_results_by_user(self, user_id: int, limit: int = 100) -> List[WordTrainResults]:
        return await self.repo.get_by_user_id(user_id, limit)
    
    async def get_results_by_word(self, word_id: int, limit: int = 100) -> List[WordTrainResults]:
        return await self.repo.get_by_word_id(word_id, limit)
    
    async def create_result(self, result_data: WordTrainResultCreate) -> WordTrainResults:
        new_result = WordTrainResults(
            name=result_data.name,
            word_accuracy=result_data.word_accuracy,
            train_words_id=result_data.train_words_id,
            user_id=result_data.user_id
        )
        return await self.repo.create(new_result)
    
    async def update_result(
        self,
        result_id: int,
        result_data: WordTrainResultUpdate
    ) -> Optional[WordTrainResults]:
        result = await self.repo.get_by_id(result_id)
        if not result:
            return None
        
        if result_data.name is not None:
            result.name = result_data.name
        if result_data.word_accuracy is not None:
            result.word_accuracy = result_data.word_accuracy
        if result_data.train_words_id is not None:
            result.train_words_id = result_data.train_words_id
        if result_data.user_id is not None:
            result.user_id = result_data.user_id
        
        return await self.repo.update(result)
    
    async def delete_result(self, result_id: int) -> bool:
        return await self.repo.delete(result_id)


class SentenceTrainResultService:
    
    def __init__(self, db: AsyncSession):
        self.repo = SentenceTrainResultRepository(db)
    
    async def get_result_by_id(self, result_id: int) -> Optional[SentenceTrainResults]:
        return await self.repo.get_by_id(result_id)
    
    async def get_results_by_user(self, user_id: int, limit: int = 100) -> List[SentenceTrainResults]:
        return await self.repo.get_by_user_id(user_id, limit)
    
    async def get_results_by_sentence(self, sentence_id: int, limit: int = 100) -> List[SentenceTrainResults]:
        return await self.repo.get_by_sentence_id(sentence_id, limit)
    
    async def create_result(self, result_data: SentenceTrainResultCreate) -> SentenceTrainResults:
        new_result = SentenceTrainResults(
            name=result_data.name,
            word_accuracy=result_data.word_accuracy,
            train_sentences_id=result_data.train_sentences_id,
            user_id=result_data.user_id
        )
        return await self.repo.create(new_result)
    
    async def update_result(
        self,
        result_id: int,
        result_data: SentenceTrainResultUpdate
    ) -> Optional[SentenceTrainResults]:
        result = await self.repo.get_by_id(result_id)
        if not result:
            return None
        
        if result_data.name is not None:
            result.name = result_data.name
        if result_data.word_accuracy is not None:
            result.word_accuracy = result_data.word_accuracy
        if result_data.train_sentences_id is not None:
            result.train_sentences_id = result_data.train_sentences_id
        if result_data.user_id is not None:
            result.user_id = result_data.user_id
        
        return await self.repo.update(result)
    
    async def delete_result(self, result_id: int) -> bool:
        return await self.repo.delete(result_id)

