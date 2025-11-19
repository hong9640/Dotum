"""
SessionPraatResult Repository
세션 단위 Praat 평균 지표 관련 DB 작업을 처리하는 Repository
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..models.session_praat_result import SessionPraatResult
from ..models.training_item import TrainingItem
from ..models.praat import PraatFeatures
from ..models.media import MediaFile, MediaType
from api.shared.repositories.base import BaseRepository


class SessionPraatResultRepository(BaseRepository[SessionPraatResult]):
    """세션 단위 Praat 평균 결과 Repository"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, SessionPraatResult)
    
    async def get_by_session_id(self, session_id: int) -> Optional[SessionPraatResult]:
        """세션 ID로 평균 Praat 결과 조회"""
        result = await self.db.execute(
            select(SessionPraatResult).where(
                SessionPraatResult.training_session_id == session_id
            )
        )
        return result.scalar_one_or_none()
    
    async def get_session_items_with_praat(self, session_id: int) -> List[tuple[TrainingItem, Optional[PraatFeatures]]]:
        """세션의 모든 아이템과 각 아이템의 Praat 분석 결과를 조회
        
        Returns:
            List[tuple[TrainingItem, Optional[PraatFeatures]]]: (아이템, Praat분석결과) 튜플 리스트
        """
        # 1. 세션의 모든 아이템을 item_index 순서로 조회
        items_stmt = (
            select(TrainingItem)
            .where(TrainingItem.training_session_id == session_id)
            .order_by(TrainingItem.item_index)
        )
        items_result = await self.db.execute(items_stmt)
        items = items_result.scalars().all()
        
        result = []
        
        # 2. 각 아이템의 Praat 분석 결과 조회
        for item in items:
            praat_feature = None
            
            # VOCAL 타입의 경우 오디오 파일에서 Praat 데이터 찾기
            # object_key 패턴: audios/{username}/{session_id}/audio_item_{item.id}.wav
            audio_media_stmt = select(MediaFile).where(
                MediaFile.media_type == MediaType.AUDIO,
                MediaFile.object_key.like(f"%audio_item_{item.id}.wav%")
            )
            audio_media_result = await self.db.execute(audio_media_stmt)
            audio_media = audio_media_result.scalar_one_or_none()
            
            if audio_media:
                # Praat 분석 결과 조회
                praat_stmt = select(PraatFeatures).where(
                    PraatFeatures.media_id == audio_media.id
                )
                praat_result = await self.db.execute(praat_stmt)
                praat_feature = praat_result.scalar_one_or_none()
            
            result.append((item, praat_feature))
        
        return result

