from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func
from sqlmodel import select
from ..schemas import TrainWordCreate, TrainWordUpdate
from ..models import TrainWords
from typing import List, Optional


class WordService:
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_all_words(self, limit: int = 10) -> List[TrainWords]:
        result = await self.db.execute(
            select(TrainWords)
            .order_by(func.random())
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_word_by_id(self, word_id: int) -> Optional[TrainWords]:
        return await self.db.get(TrainWords, word_id)
    
    async def get_word_by_text(self, word: str) -> Optional[TrainWords]:
        #중복 체크크
        result = await self.db.execute(
            select(TrainWords).where(TrainWords.word == word)
        )
        return result.scalar_one_or_none()
    
    async def create_word(self, word_data: TrainWordCreate) -> TrainWords:
        # 중복 체크
        existing_word = await self.get_word_by_text(word_data.word)
        if existing_word:
            raise ValueError(f"단어 '{word_data.word}'는 이미 존재합니다.")
        
        new_word = TrainWords(word=word_data.word)
        self.db.add(new_word)
        await self.db.commit()
        await self.db.refresh(new_word)
        return new_word
    
    async def update_word(self, word_id: int, word_data: TrainWordUpdate) -> Optional[TrainWords]:
        word = await self.db.get(TrainWords, word_id)
        if not word:
            return None
        
        # 중복 체크 (자기 자신 제외)
        existing_word = await self.get_word_by_text(word_data.word)
        if existing_word and existing_word.id != word_id:
            raise ValueError(f"{word_data.word}는 이미 존재합니다.")
        
        word.word = word_data.word
        await self.db.commit()
        await self.db.refresh(word)
        return word
    
    async def delete_word(self, word_id: int) -> bool:
        word = await self.db.get(TrainWords, word_id)
        if not word:
            return False
        await self.db.delete(word)
        await self.db.commit()
        return True
