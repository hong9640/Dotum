from sqlalchemy.ext.asyncio import AsyncSession
from ..schemas import TrainWordCreate, TrainWordUpdate
from ..models import TrainWords
from ..repositories import WordRepository
from typing import List, Optional


class WordService:
    """단어 비즈니스 로직을 담당하는 Service"""
    
    def __init__(self, db: AsyncSession):
        self.repo = WordRepository(db)
    
    async def get_random_words(self, limit: int = 1) -> List[TrainWords]:
        """랜덤하게 단어를 가져옴 (기본 1개)"""
        return await self.repo.get_random(limit)
    
    async def get_word_by_id(self, word_id: int) -> Optional[TrainWords]:
        """ID로 단어 조회"""
        return await self.repo.get_by_id(word_id)
    
    async def get_word_by_text(self, word: str) -> Optional[TrainWords]:
        """텍스트로 단어 조회 (중복 체크용)"""
        return await self.repo.get_by_text(word)
    
    async def create_word(self, word_data: TrainWordCreate) -> TrainWords:
        """단어 생성 (중복 체크 포함)"""
        # 중복 체크
        existing_word = await self.repo.get_by_text(word_data.word)
        if existing_word:
            raise ValueError(f"단어 '{word_data.word}'는 이미 존재합니다.")
        
        new_word = TrainWords(word=word_data.word)
        return await self.repo.create(new_word)
    
    async def update_word(self, word_id: int, word_data: TrainWordUpdate) -> Optional[TrainWords]:
        """단어 수정 (중복 체크 포함)"""
        word = await self.repo.get_by_id(word_id)
        if not word:
            return None
        
        # 중복 체크 (자기 자신 제외)
        existing_word = await self.repo.get_by_text(word_data.word)
        if existing_word and existing_word.id != word_id:
            raise ValueError(f"{word_data.word}는 이미 존재합니다.")
        
        word.word = word_data.word
        return await self.repo.update(word)
    
    async def delete_word(self, word_id: int) -> bool:
        """단어 삭제"""
        return await self.repo.delete(word_id)
