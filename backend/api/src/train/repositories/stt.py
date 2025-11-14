"""
STT Results Repository
STT 결과 관련 DB 작업을 처리하는 Repository
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.training_item_stt_results import TrainingItemSttResults
from .base import BaseRepository


class SttResultsRepository(BaseRepository[TrainingItemSttResults]):
    """STT 결과 Repository"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, TrainingItemSttResults)
    
    async def create_and_flush(
        self,
        training_item_id: int,
        ai_model_id: int,
        stt_result: str
    ) -> TrainingItemSttResults:
        """STT 결과 생성 (flush만 수행, commit은 호출자가 담당)"""
        stt_record = TrainingItemSttResults(
            training_item_id=training_item_id,
            ai_model_id=ai_model_id,
            stt_result=stt_result
        )
        self.db.add(stt_record)
        await self.db.flush()
        return stt_record
    
    async def get_by_training_item_id(
        self,
        training_item_id: int
    ) -> Optional[TrainingItemSttResults]:
        """특정 훈련 아이템의 STT 결과 조회 (최신 결과 반환)"""
        stmt = select(TrainingItemSttResults).where(
            TrainingItemSttResults.training_item_id == training_item_id
        ).order_by(TrainingItemSttResults.created_at.desc())
        
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def get_all_by_training_item_id(
        self,
        training_item_id: int
    ) -> List[TrainingItemSttResults]:
        """특정 훈련 아이템의 모든 STT 결과 조회"""
        stmt = select(TrainingItemSttResults).where(
            TrainingItemSttResults.training_item_id == training_item_id
        ).order_by(TrainingItemSttResults.created_at.desc())
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_by_session_id(
        self,
        session_id: int
    ) -> List[TrainingItemSttResults]:
        """세션의 모든 STT 결과 조회 (세션 완료 확인용)"""
        from ..models.training_item import TrainingItem
        
        stmt = select(TrainingItemSttResults).join(
            TrainingItem,
            TrainingItem.id == TrainingItemSttResults.training_item_id
        ).where(
            TrainingItem.session_id == session_id
        ).order_by(TrainingItem.item_index)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()

