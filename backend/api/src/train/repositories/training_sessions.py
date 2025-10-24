from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, func, and_
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from datetime import datetime, date

from ..models.training_session import TrainingSession, TrainingType, TrainingSessionStatus
from ..models.training_item import TrainingItem
from .base import BaseRepository


class TrainingSessionRepository(BaseRepository[TrainingSession]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, TrainingSession)
    
    def _get_base_session_query(self, include_items: bool = True):
        """기본 세션 쿼리 생성"""
        stmt = select(TrainingSession)
        if include_items:
            stmt = stmt.options(selectinload(TrainingSession.training_items))
        return stmt

    async def create_session(
        self, 
        user_id: int, 
        session_name: str,
        type: TrainingType, 
        total_items: int,
        training_date: Optional[datetime] = None,
        session_metadata: Optional[Dict[str, Any]] = None
    ) -> TrainingSession:
        """훈련 세션 생성 (바로 시작)"""
        now = datetime.now()
        session = TrainingSession(
            user_id=user_id,
            session_name=session_name,
            type=type,
            status=TrainingSessionStatus.IN_PROGRESS,  # 바로 IN_PROGRESS로
            total_items=total_items,
            completed_items=0,
            current_item_index=0,
            training_date=training_date or now,
            session_metadata=session_metadata or {},
            started_at=now  # 시작 시간도 바로 설정
        )
        self.db.add(session)
        await self.db.flush()  # ID를 얻기 위해 flush
        return session

    async def create_item(
        self, session_id: int, item_index: int, 
        word_id: Optional[int] = None, sentence_id: Optional[int] = None
    ) -> TrainingItem:
        """훈련 아이템 생성"""
        item = TrainingItem(
            training_session_id=session_id,
            item_index=item_index,
            word_id=word_id,
            sentence_id=sentence_id,
            is_completed=False
        )
        self.db.add(item)
        await self.db.flush()
        return item

    async def get_user_sessions(
        self, 
        user_id: int, 
        type: Optional[TrainingType] = None,
        status: Optional[TrainingSessionStatus] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[TrainingSession]:
        """사용자의 훈련 세션 목록 조회 (필터링 지원)"""
        stmt = self._get_base_session_query(True)
        stmt = stmt.where(TrainingSession.user_id == user_id)
        
        if type:
            stmt = stmt.where(TrainingSession.type == type)
        if status:
            stmt = stmt.where(TrainingSession.status == status)
            
        stmt = stmt.order_by(TrainingSession.created_at.desc())
        
        if limit:
            stmt = stmt.limit(limit).offset(offset)
            
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_session(self, session_id: int, user_id: int) -> Optional[TrainingSession]:
        """특정 훈련 세션 조회 (소유권 확인)"""
        stmt = self._get_base_session_query(True)
        stmt = stmt.where(
            TrainingSession.id == session_id,
            TrainingSession.user_id == user_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_session_by_id(self, session_id: int) -> Optional[TrainingSession]:
        """ID로 훈련 세션 조회 (소유권 확인 없음)"""
        stmt = self._get_base_session_query(True)
        stmt = stmt.where(TrainingSession.id == session_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_sessions_by_date(
        self, 
        user_id: int, 
        training_date: date,
        type: Optional[TrainingType] = None
    ) -> List[TrainingSession]:
        """특정 날짜의 훈련 세션 조회"""
        stmt = self._get_base_session_query(True)
        stmt = stmt.where(
            TrainingSession.user_id == user_id,
            func.date(TrainingSession.training_date) == training_date
        )
        
        if type:
            stmt = stmt.where(TrainingSession.type == type)
            
        stmt = stmt.order_by(TrainingSession.created_at.desc())
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_calendar_data(
        self, 
        user_id: int, 
        year: int, 
        month: int,
        type: Optional[TrainingType] = None
    ) -> Dict[str, int]:
        """월별 훈련 달력 데이터 조회"""
        stmt = (
            select(
                func.date(TrainingSession.training_date).label('date'),
                func.count(TrainingSession.id).label('count')
            )
            .where(
                TrainingSession.user_id == user_id,
                func.extract('year', TrainingSession.training_date) == year,
                func.extract('month', TrainingSession.training_date) == month
            )
        )
        
        if type:
            stmt = stmt.where(TrainingSession.type == type)
            
        stmt = stmt.group_by(func.date(TrainingSession.training_date))
        
        result = await self.db.execute(stmt)
        
        calendar_data = {}
        for row in result:
            calendar_data[str(row.date)] = row.count
        
        return calendar_data


    async def update_status(
        self, 
        session_id: int, 
        status: TrainingSessionStatus,
        user_id: Optional[int] = None
    ) -> bool:
        """세션 상태 업데이트"""
        where_conditions = [TrainingSession.id == session_id]
        if user_id:
            where_conditions.append(TrainingSession.user_id == user_id)
        
        update_data = {
            'status': status,
            'updated_at': func.now()
        }
        
        if status == TrainingSessionStatus.IN_PROGRESS:
            update_data['started_at'] = func.now()
        elif status == TrainingSessionStatus.COMPLETED:
            update_data['completed_at'] = func.now()
        
        result = await self.db.execute(
            update(TrainingSession)
            .where(and_(*where_conditions))
            .values(**update_data)
        )
        
        return result.rowcount > 0
    
    async def update_progress(
        self, 
        session_id: int, 
        completed_items: int,
        current_item_index: Optional[int] = None
    ) -> bool:
        """세션 진행률 업데이트"""
        # 세션 정보 조회
        session = await self.get_session_by_id(session_id)
        if not session:
            return False
            
        progress_percentage = completed_items / session.total_items if session.total_items > 0 else 0.0
        
        update_data = {
            'completed_items': completed_items,
            'progress_percentage': progress_percentage,
            'updated_at': func.now()
        }
        
        if current_item_index is not None:
            update_data['current_item_index'] = current_item_index
        
        # 자동 상태 전환
        if progress_percentage == 1.0:
            update_data['status'] = TrainingSessionStatus.COMPLETED
            update_data['completed_at'] = func.now()
        
        result = await self.db.execute(
            update(TrainingSession)
            .where(TrainingSession.id == session_id)
            .values(**update_data)
        )
        
        return result.rowcount > 0
    

    async def delete_session(self, session_id: int, user_id: int) -> bool:
        """훈련 세션 삭제"""
        # 세션 소유권 확인
        session = await self.get_session(session_id, user_id)
        if not session:
            return False
        
        # 관련 아이템들도 함께 삭제 (CASCADE로 자동 삭제되지만 명시적으로)
        items_stmt = delete(TrainingItem).where(TrainingItem.training_session_id == session_id)
        await self.db.execute(items_stmt)
        
        # 세션 삭제
        session_stmt = delete(TrainingSession).where(TrainingSession.id == session_id)
        result = await self.db.execute(session_stmt)
        
        return result.rowcount > 0
