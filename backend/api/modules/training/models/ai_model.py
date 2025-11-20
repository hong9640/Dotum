from sqlmodel import SQLModel, Field
from datetime import datetime
from api.core.time_utils import now_kst


class AIModel(SQLModel, table=True):
    """AI 모델 버전 테이블"""
    __tablename__ = "ai_models"
    
    id: int = Field(default=None, primary_key=True)
    version: str = Field(unique=True, index=True, description="모델 버전 (예: gpt-5)")
    created_at: datetime = Field(default_factory=now_kst)

