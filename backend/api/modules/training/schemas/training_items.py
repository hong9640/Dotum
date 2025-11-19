from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from api.modules.training.schemas.praat import PraatFeaturesResponse
from datetime import datetime


class FeedbackResponse(BaseModel):
    """피드백 응답 객체 (프론트엔드에서 키로 접근 가능)"""
    item: Optional[str] = Field(default=None, description="아이템 피드백")
    vowel_distortion: Optional[str] = Field(default=None, description="모음 왜곡도 피드백 (NFCD 기반, F1, F2 포먼트 값)")
    sound_stability: Optional[str] = Field(default=None, description="소리의 안정도 피드백 (CPP 기반)")
    voice_clarity: Optional[str] = Field(default=None, description="음성 일탈도 피드백 (HNR 기반)")
    voice_health: Optional[str] = Field(default=None, description="음성 건강지수 피드백 (CSID 기반)")
    
    model_config = ConfigDict(from_attributes=True)


class TrainingItemResponse(BaseModel):
    """훈련 아이템 응답"""
    item_id: int = Field(description="아이템 ID")
    training_session_id: int
    item_index: int
    word_id: Optional[int] = None
    sentence_id: Optional[int] = None
    word: Optional[str] = None
    sentence: Optional[str] = None
    is_completed: bool
    score: Optional[float] = None
    feedback: Optional[str] = None
    video_url: Optional[str] = None
    audio_url: Optional[str] = None
    image_url: Optional[str] = None
    composited_video_url: Optional[str] = None
    media_file_id: Optional[int] = None
    composited_media_file_id: Optional[int] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=False)


class CurrentItemResponse(BaseModel):
    """현재 훈련 아이템 응답"""
    item_id: int = Field(description="아이템 ID")
    item_index: int
    word_id: Optional[int] = None
    sentence_id: Optional[int] = None
    word: Optional[str] = None
    sentence: Optional[str] = None
    is_completed: bool
    feedback: Optional[FeedbackResponse] = Field(
        default=None,
        description="피드백 객체 (프론트엔드에서 키로 접근 가능)"
    )
    video_url: Optional[str] = None
    composited_video_url: Optional[str] = None
    media_file_id: Optional[int] = None
    composited_media_file_id: Optional[int] = None
    has_next: bool
    praat: Optional[PraatFeaturesResponse] = None
    integrate_voice_url: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=False)


class CompleteItemRequest(BaseModel):
    """아이템 완료 요청"""
    video_url: str
    media_file_id: Optional[int] = None
