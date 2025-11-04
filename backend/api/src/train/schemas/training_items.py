from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TrainingItemResponse(BaseModel):
    """훈련 아이템 응답"""
    id: int
    training_session_id: int
    item_index: int
    word_id: Optional[int] = None
    sentence_id: Optional[int] = None
    is_completed: bool
    video_url: Optional[str] = None
    media_file_id: Optional[int] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CurrentItemResponse(BaseModel):
    """현재 훈련 아이템 응답"""
    id: int
    item_index: int
    word_id: Optional[int] = None
    sentence_id: Optional[int] = None
    word: Optional[str] = None
    sentence: Optional[str] = None
    is_completed: bool
    video_url: Optional[str] = None
    media_file_id: Optional[int] = None
    has_next: bool
    
    class Config:
        from_attributes = True


class CompleteItemRequest(BaseModel):
    """아이템 완료 요청"""
    video_url: str
    media_file_id: Optional[int] = None
