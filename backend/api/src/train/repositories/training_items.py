from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime

from ..models.training_item import TrainingItem
from ..models.training_session import TrainingType
from .base import BaseRepository


class TrainingItemRepository(BaseRepository[TrainingItem]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, TrainingItem)
    
    def _get_base_query(self, include_relations: bool = True):
        """기본 쿼리 생성 (관계 포함 여부 선택)"""
        stmt = select(TrainingItem)
        if include_relations:
            stmt = stmt.options(
                selectinload(TrainingItem.word),
                selectinload(TrainingItem.sentence),
                selectinload(TrainingItem.media_file)
            )
        return stmt

    async def create_batch(
        self, 
        session_id: int, 
        item_ids: List[int],
        training_type: TrainingType
    ) -> List[TrainingItem]:
        """훈련 아이템들을 일괄 생성"""
        items = []
        
        for index, item_id in enumerate(item_ids):
            item_data = {
                'training_session_id': session_id,
                'item_index': index,
                'is_completed': False
            }
            
            # 훈련 타입에 따라 적절한 ID 설정
            if training_type == TrainingType.WORD:
                item_data['word_id'] = item_id
            elif training_type == TrainingType.SENTENCE:
                item_data['sentence_id'] = item_id
            
            item = TrainingItem(**item_data)
            self.db.add(item)
            items.append(item)
        
        await self.db.flush()
        return items

    async def get_session_items(
        self, 
        session_id: int,
        include_relations: bool = True
    ) -> List[TrainingItem]:
        """세션의 모든 아이템 조회"""
        stmt = self._get_base_query(include_relations)
        stmt = stmt.where(TrainingItem.training_session_id == session_id)
        stmt = stmt.order_by(TrainingItem.item_index)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_item(
        self, 
        session_id: int, 
        item_id: int,
        include_relations: bool = True
    ) -> Optional[TrainingItem]:
        """특정 훈련 아이템 조회"""
        stmt = self._get_base_query(include_relations)
        stmt = stmt.where(
            TrainingItem.id == item_id,
            TrainingItem.training_session_id == session_id
        )
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_item_by_index(
        self,
        session_id: int,
        item_index: int,
        include_relations: bool = True
    ) -> Optional[TrainingItem]:
        """item_index로 특정 훈련 아이템 조회"""
        stmt = self._get_base_query(include_relations)
        stmt = stmt.where(
            TrainingItem.training_session_id == session_id,
            TrainingItem.item_index == item_index
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_items_by_status(
        self, 
        session_id: int,
        is_completed: bool,
        include_relations: bool = True
    ) -> List[TrainingItem]:
        """상태별 아이템 조회 (완료/미완료)"""
        stmt = self._get_base_query(include_relations)
        stmt = stmt.where(
            TrainingItem.training_session_id == session_id,
            TrainingItem.is_completed == is_completed
        )
        stmt = stmt.order_by(TrainingItem.item_index)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_next_item(
        self, 
        session_id: int, 
        current_index: int
    ) -> Optional[TrainingItem]:
        """다음 훈련 아이템 조회"""
        stmt = self._get_base_query(True)
        stmt = stmt.where(
            TrainingItem.training_session_id == session_id,
            TrainingItem.item_index > current_index,
            TrainingItem.is_completed == False
        )
        stmt = stmt.order_by(TrainingItem.item_index).limit(1)
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def complete_item(
        self, 
        item_id: int, 
        video_url: str,
        media_file_id: Optional[int] = None,
        is_completed: bool = True,
        audio_url: Optional[str] = None
    ) -> Optional[TrainingItem]:
        """아이템 완료 처리"""
        item = await self.get_by_id(item_id)
        if not item:
            return None
        
        original_completed = item.is_completed
        item.is_completed = is_completed
        item.video_url = video_url
        item.media_file_id = media_file_id
        if audio_url is not None:
            item.audio_url = audio_url
        # 완료 상태 전환일 때만 completed_at 갱신
        if not original_completed and is_completed:
            item.completed_at = datetime.now()
        item.updated_at = datetime.now()
        
        return item
    
    async def get_current_item(
        self, 
        session_id: int,
        include_relations: bool = True
    ) -> Optional[TrainingItem]:
        """현재 세션의 진행 중인 아이템 조회"""
        stmt = self._get_base_query(include_relations)
        stmt = stmt.where(
            TrainingItem.training_session_id == session_id,
            TrainingItem.is_completed == False
        )
        stmt = stmt.order_by(TrainingItem.item_index).limit(1)
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_completion_stats(self, session_id: int) -> dict:
        """세션 완료 통계 조회"""
        # 한 번의 쿼리로 통계 계산
        stmt = select(
            func.count(TrainingItem.id).label('total'),
            func.sum(func.case((TrainingItem.is_completed == True, 1), else_=0)).label('completed')
        ).where(TrainingItem.training_session_id == session_id)
        
        result = await self.db.execute(stmt)
        row = result.first()
        
        total_items = row.total or 0
        completed_items = row.completed or 0
        progress_percentage = (completed_items / total_items * 100) if total_items > 0 else 0.0
        
        return {
            'total_items': total_items,
            'completed_items': completed_items,
            'pending_items': total_items - completed_items,
            'progress_percentage': progress_percentage
        }

    async def delete_session_items(self, session_id: int) -> bool:
        """세션의 모든 아이템 삭제"""
        stmt = delete(TrainingItem).where(TrainingItem.training_session_id == session_id)
        result = await self.db.execute(stmt)
        return result.rowcount > 0

    async def get_items_by_type(
        self, 
        session_id: int, 
        training_type: TrainingType
    ) -> List[TrainingItem]:
        """타입별 아이템 조회"""
        stmt = self._get_base_query(True)
        stmt = stmt.where(TrainingItem.training_session_id == session_id)
        
        # 타입에 따른 필터링
        if training_type == TrainingType.WORD:
            stmt = stmt.where(TrainingItem.word_id.isnot(None))
        elif training_type == TrainingType.SENTENCE:
            stmt = stmt.where(TrainingItem.sentence_id.isnot(None))
        
        stmt = stmt.order_by(TrainingItem.item_index)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
