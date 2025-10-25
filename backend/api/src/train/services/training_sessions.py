from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from datetime import datetime, date

from ..models.training_session import TrainingSession, TrainingType, TrainingSessionStatus
from ..repositories.training_sessions import TrainingSessionRepository
from ..repositories.training_items import TrainingItemRepository
from ..schemas.training_sessions import (
    TrainingSessionCreate,
    TrainingSessionUpdate,
    TrainingSessionResponse,
    TrainingSessionStatusUpdate,
    CalendarResponse,
    DailyTrainingResponse
)


class TrainingSessionService:
    """통합된 훈련 세션 서비스"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = TrainingSessionRepository(db)
        self.item_repo = TrainingItemRepository(db)
    
    async def create_training_session(
        self, 
        user_id: int, 
        session_data: TrainingSessionCreate
    ) -> TrainingSession:
        """훈련 세션 생성"""
        # 랜덤 아이템 ID들 가져오기
        item_ids = await self._get_random_item_ids(session_data.type, session_data.item_count)
        
        if not item_ids:
            raise ValueError(f"해당 타입({session_data.type})의 아이템을 찾을 수 없습니다")
        
        # 훈련 세션 생성
        training_session = await self.repo.create_session(
            user_id=user_id,
            session_name=session_data.session_name,
            type=session_data.type,
            total_items=len(item_ids),
            training_date=session_data.training_date,
            session_metadata=session_data.session_metadata
        )
        
        # 훈련 아이템들 생성
        await self.item_repo.create_batch(
            training_session.id, 
            item_ids,
            session_data.type
        )
        
        await self.db.commit()
        return training_session
    
    async def _get_random_item_ids(self, training_type: TrainingType, count: int) -> List[int]:
        """훈련 타입에 따른 랜덤 아이템 ID들 가져오기"""
        if training_type == TrainingType.WORD:
            from ..repositories.words import WordRepository
            word_repo = WordRepository(self.db)
            words = await word_repo.get_random(count)
            return [word.id for word in words]
        
        elif training_type == TrainingType.SENTENCE:
            from ..repositories.sentences import SentenceRepository
            sentence_repo = SentenceRepository(self.db)
            sentences = await sentence_repo.get_random(count)
            return [sentence.id for sentence in sentences]
        
        else:
            # 다른 타입들은 추후 구현
            return []
    
    async def get_training_session(
        self, 
        session_id: int, 
        user_id: int
    ) -> Optional[TrainingSession]:
        """훈련 세션 조회"""
        return await self.repo.get_session(session_id, user_id)
    
    async def get_user_training_sessions(
        self, 
        user_id: int,
        type: Optional[TrainingType] = None,
        status: Optional[TrainingSessionStatus] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[TrainingSession]:
        """사용자의 훈련 세션 목록 조회"""
        return await self.repo.get_user_sessions(
            user_id=user_id,
            type=type,
            status=status,
            limit=limit,
            offset=offset
        )
    
    async def get_training_sessions_by_date(
        self, 
        user_id: int, 
        training_date: date,
        type: Optional[TrainingType] = None
    ) -> List[TrainingSession]:
        """특정 날짜의 훈련 세션 조회"""
        return await self.repo.get_sessions_by_date(
            user_id=user_id,
            training_date=training_date,
            type=type
        )
    
    async def get_training_calendar(
        self, 
        user_id: int, 
        year: int, 
        month: int,
        type: Optional[TrainingType] = None
    ) -> Dict[str, int]:
        """월별 훈련 달력 조회"""
        return await self.repo.get_calendar_data(
            user_id=user_id,
            year=year,
            month=month,
            type=type
        )
    
    
    async def complete_training_session(
        self, 
        session_id: int, 
        user_id: int
    ) -> Optional[TrainingSession]:
        """훈련 세션 완료"""
        session = await self.get_training_session(session_id, user_id)
        if not session:
            return None
        
        if not session.can_complete():
            raise ValueError("세션을 완료할 수 없습니다. 현재 상태를 확인해주세요.")
        
        # 세션 상태를 완료로 변경
        await self.repo.update_status(
            session_id, 
            TrainingSessionStatus.COMPLETED,
            user_id
        )
        await self.db.commit()
        
        return await self.get_training_session(session_id, user_id)
    
    
    async def update_session_status(
        self, 
        session_id: int, 
        user_id: int,
        status_update: TrainingSessionStatusUpdate
    ) -> Optional[TrainingSession]:
        """세션 상태 업데이트 (유연한 상태 전환)"""
        session = await self.get_training_session(session_id, user_id)
        if not session:
            return None
        
        # 상태 전환 검증
        if not self._is_valid_status_transition(session.status, status_update.status):
            raise ValueError(f"상태 전환이 불가능합니다: {session.status} -> {status_update.status}")
        
        await self.repo.update_status(
            session_id, 
            status_update.status,
            user_id
        )
        await self.db.commit()
        
        return await self.get_training_session(session_id, user_id)
    
    async def complete_training_item(
        self, 
        session_id: int, 
        item_id: int, 
        video_url: str, 
        media_file_id: Optional[int],
        is_completed: bool,
        user_id: int
    ) -> Optional[TrainingSession]:
        """훈련 아이템 완료 처리 (자동 진행률 업데이트)"""
        # 아이템 완료 처리
        await self.item_repo.complete_item(item_id, video_url, media_file_id, is_completed)
        
        # 세션 진행률 자동 업데이트
        completed_count = await self.repo.get_completed_items_count(session_id)
        await self.repo.update_progress(session_id, completed_count)
        
        # 다음 아이템으로 이동
        await self.repo.move_to_next_item(session_id)
        
        await self.db.commit()
        
        return await self.get_training_session(session_id, user_id)
    
    async def get_current_item(
        self,
        session_id: int,
        user_id: int
    ):
        """현재 세션의 진행 중인 아이템 조회"""
        # 세션 소유권 확인
        session = await self.get_training_session(session_id, user_id)
        if not session:
            return None
        
        # 현재 아이템 조회
        current_item = await self.item_repo.get_current_item(session_id, include_relations=True)
        
        if not current_item:
            return None
        
        # 다음 아이템 존재 여부 확인
        has_next = await self.item_repo.get_next_item(session_id, current_item.item_index) is not None
        
        return {
            'item': current_item,
            'has_next': has_next
        }
    
    async def delete_training_session(
        self, 
        session_id: int, 
        user_id: int
    ) -> bool:
        """훈련 세션 삭제"""
        return await self.repo.delete_session(session_id, user_id)
    
    def _is_valid_status_transition(
        self, 
        current_status: TrainingSessionStatus, 
        new_status: TrainingSessionStatus
    ) -> bool:
        """상태 전환 유효성 검증"""
        valid_transitions = {
            TrainingSessionStatus.IN_PROGRESS: [
                TrainingSessionStatus.COMPLETED,
                TrainingSessionStatus.CANCELLED
            ],
            TrainingSessionStatus.COMPLETED: [],  # 완료된 세션은 상태 변경 불가
            TrainingSessionStatus.CANCELLED: []   # 취소된 세션은 상태 변경 불가
        }
        
        return new_status in valid_transitions.get(current_status, [])