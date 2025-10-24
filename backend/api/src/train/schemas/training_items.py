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
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
