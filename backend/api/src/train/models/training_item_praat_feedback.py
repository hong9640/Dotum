"""
개별 훈련 아이템의 Praat 분석 피드백 모델

각 아이템별로 세부적인 음성 분석 피드백을 저장
"""
from sqlmodel import SQLModel, Field, Relationship, Column
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Text

if TYPE_CHECKING:
    from api.src.train.models.praat import PraatFeatures
    from api.src.train.models.ai_model import AIModel


class TrainItemPraatFeedback(SQLModel, table=True):
    """개별 훈련 아이템의 Praat 분석 피드백 (vocal 타입 전용)"""
    __tablename__ = "training_item_praat_feedback"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    praat_features_id: int = Field(index=True, description="PraatFeatures ID (논리 FK)")
    ai_model_id: Optional[int] = Field(default=None, index=True, description="AI 모델 ID (논리 FK)")
    
    # 아이템 피드백
    item_feedback: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="아이템 피드백"
    )
    
    # 메타 정보
    created_at: datetime = Field(default_factory=datetime.now)
    
    # 관계 (논리 FK, 1:1)
    praat_features: Optional["PraatFeatures"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "TrainItemPraatFeedback.praat_features_id==foreign(PraatFeatures.id)",
            "foreign_keys": "[TrainItemPraatFeedback.praat_features_id]",
            "uselist": False,  # 1:1 관계
        }
    )
    
    ai_model: Optional["AIModel"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "TrainItemPraatFeedback.ai_model_id==foreign(AIModel.id)",
            "foreign_keys": "[TrainItemPraatFeedback.ai_model_id]",
            "overlaps": "ai_model",
        }
    )

