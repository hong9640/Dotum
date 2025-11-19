"""
LLM 피드백 Repository

데이터베이스 접근 로직만 담당
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from api.src.train.models.training_session_praat_feedback import TrainSessionPraatFeedback
from api.src.train.models.training_item_praat_feedback import TrainItemPraatFeedback
from api.src.train.models.session_praat_result import SessionPraatResult
from api.src.train.models.praat import PraatFeatures
from api.src.train.models.ai_model import AIModel
from api.core.logging import get_logger

logger = get_logger(__name__)


class FeedbackRepository:
    """피드백 데이터 접근 레이어"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ==================== AIModel ====================
    
    async def get_or_create_ai_model(self, version: str) -> AIModel:
        """
        AI 모델 버전을 조회하거나 없으면 생성
        
        Args:
            version: 모델 버전 문자열 (예: "gpt-5-mini")
            
        Returns:
            AIModel 인스턴스
        """
        # 1. 기존 모델 조회
        stmt = select(AIModel).where(AIModel.version == version)
        result = await self.db.execute(stmt)
        existing_model = result.scalar_one_or_none()
        
        if existing_model:
            return existing_model
        
        # 2. 없으면 새로 생성
        new_model = AIModel(version=version)
        self.db.add(new_model)
        await self.db.commit()
        await self.db.refresh(new_model)
        
        logger.info(f"AIModel created: id={new_model.id}, version={version}")
        return new_model
    
    # ==================== SessionPraatResult ====================
    
    async def get_session_praat_result_by_session_id(
        self, 
        session_id: int
    ) -> Optional[SessionPraatResult]:
        """
        세션 ID로 SessionPraatResult 조회
        
        Args:
            session_id: 훈련 세션 ID
            
        Returns:
            SessionPraatResult 또는 None
        """
        stmt = select(SessionPraatResult).where(
            SessionPraatResult.training_session_id == session_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    # ==================== TrainSessionPraatFeedback ====================
    
    async def get_session_feedback_by_praat_result_id(
        self,
        session_praat_result_id: int
    ) -> Optional[TrainSessionPraatFeedback]:
        """
        SessionPraatResult ID로 세션 피드백 조회
        
        Args:
            session_praat_result_id: SessionPraatResult ID
            
        Returns:
            TrainSessionPraatFeedback 또는 None
        """
        stmt = select(TrainSessionPraatFeedback).where(
            TrainSessionPraatFeedback.session_praat_result_id == session_praat_result_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create_session_feedback(
        self,
        session_praat_result_id: int,
        feedback_text: str,
        ai_model_id: int
    ) -> TrainSessionPraatFeedback:
        """
        세션 피드백 생성
        
        Args:
            session_praat_result_id: SessionPraatResult ID
            feedback_text: 피드백 텍스트
            ai_model_id: AI 모델 ID (FK)
            
        Returns:
            생성된 TrainSessionPraatFeedback
        """
        feedback = TrainSessionPraatFeedback(
            session_praat_result_id=session_praat_result_id,
            feedback_text=feedback_text,
            ai_model_id=ai_model_id
        )
        self.db.add(feedback)
        await self.db.commit()
        await self.db.refresh(feedback)
        
        logger.info(f"Session feedback created: id={feedback.id}, session_praat_result_id={session_praat_result_id}")
        return feedback
    
    # ==================== PraatFeatures ====================
    
    async def get_praat_features_by_id(
        self,
        praat_features_id: int
    ) -> Optional[PraatFeatures]:
        """
        ID로 PraatFeatures 조회
        
        Args:
            praat_features_id: PraatFeatures ID
            
        Returns:
            PraatFeatures 또는 None
        """
        stmt = select(PraatFeatures).where(PraatFeatures.id == praat_features_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    # ==================== TrainItemPraatFeedback ====================
    
    async def get_item_feedback_by_praat_features_id(
        self,
        praat_features_id: int
    ) -> Optional[TrainItemPraatFeedback]:
        """
        PraatFeatures ID로 아이템 피드백 조회
        
        Args:
            praat_features_id: PraatFeatures ID
            
        Returns:
            TrainItemPraatFeedback 또는 None
        """
        stmt = select(TrainItemPraatFeedback).where(
            TrainItemPraatFeedback.praat_features_id == praat_features_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create_item_feedback(
        self,
        praat_features_id: int,
        item_feedback: Optional[str],
        ai_model_id: int,
        vowel_distortion_feedback: Optional[str] = None,
        sound_stability_feedback: Optional[str] = None,
        voice_clarity_feedback: Optional[str] = None,
        voice_health_feedback: Optional[str] = None,
        overall_feedback: Optional[str] = None
    ) -> TrainItemPraatFeedback:
        """
        아이템 피드백 생성
        
        Args:
            praat_features_id: PraatFeatures ID
            item_feedback: 아이템 피드백
            ai_model_id: AI 모델 ID (FK)
            vowel_distortion_feedback: 모음 왜곡도 피드백 (NFCD 기반)
            sound_stability_feedback: 소리의 안정도 피드백 (CPP 기반)
            voice_clarity_feedback: 음성 맑음도 피드백 (HNR 기반)
            voice_health_feedback: 음성 건강지수 피드백 (CSID 기반)
            overall_feedback: 전체 종합 피드백
            
        Returns:
            생성된 TrainItemPraatFeedback
        """
        feedback = TrainItemPraatFeedback(
            praat_features_id=praat_features_id,
            item_feedback=item_feedback,
            ai_model_id=ai_model_id,
            vowel_distortion_feedback=vowel_distortion_feedback,
            sound_stability_feedback=sound_stability_feedback,
            voice_clarity_feedback=voice_clarity_feedback,
            voice_health_feedback=voice_health_feedback,
            overall_feedback=overall_feedback
        )
        self.db.add(feedback)
        await self.db.commit()
        await self.db.refresh(feedback)
        
        logger.info(f"Item feedback created: id={feedback.id}, praat_features_id={praat_features_id}")
        return feedback

