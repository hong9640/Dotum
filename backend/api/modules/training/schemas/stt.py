"""
STT Results Schema
STT 결과 관련 스키마 정의
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class SttResultResponse(BaseModel):
    """STT 결과 응답"""
    id: int = Field(description="STT 결과 ID")
    training_item_id: int = Field(description="훈련 아이템 ID")
    ai_model_id: int = Field(description="AI 모델 ID")
    stt_result: str = Field(description="STT 변환 결과")
    created_at: datetime = Field(description="생성 시간")
    
    model_config = ConfigDict(from_attributes=True)

