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


class TrainItemPraatFeedback(SQLModel, table=True):
    """개별 훈련 아이템의 Praat 분석 피드백 (vocal 타입 전용)"""
    __tablename__ = "train_item_praat_feedback"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    praat_features_id: int = Field(index=True, description="PraatFeatures ID (논리 FK)")
    
    # 세부 피드백 내용
    vowel_distortion_feedback: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="모음 왜곡도 피드백 (F1, F2 기반)"
    )
    sound_stability_feedback: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="소리의 안정도 피드백 (CPP 기반)"
    )
    voice_clarity_feedback: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="음성 맑음도 피드백 (HNR 기반)"
    )
    voice_health_feedback: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="음성 건강지수 피드백 (CSID 기반)"
    )
    
    # 종합 피드백
    overall_feedback: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="전체 종합 피드백"
    )
    
    # 메타 정보
    model_version: str = Field(description="LLM 모델 버전")
    created_at: datetime = Field(default_factory=datetime.now)
    
    # 관계 (논리 FK, 1:1)
    praat_features: Optional["PraatFeatures"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "TrainItemPraatFeedback.praat_features_id==foreign(PraatFeatures.id)",
            "foreign_keys": "[TrainItemPraatFeedback.praat_features_id]",
            "uselist": False,  # 1:1 관계
        }
    )

