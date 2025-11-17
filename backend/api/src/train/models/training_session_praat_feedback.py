from sqlmodel import SQLModel, Field, Relationship, Column
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Text

if TYPE_CHECKING:
    from api.src.train.models.session_praat_result import SessionPraatResult
    from api.src.train.models.ai_model import AIModel

class TrainSessionPraatFeedback(SQLModel, table=True):
    """훈련 세션 단위 Praat 평균 지표 저장 (vocal 타입 전용)"""
    __tablename__ = "train_session_praat_feedback"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    session_praat_result_id: int = Field(index=True, description="SessionPraatResult ID (논리 FK)")
    ai_model_id: int = Field(index=True, description="AI 모델 ID (논리 FK)")
    
    feedback_text: str = Field(sa_column=Column(Text), description="LLM 피드백 내용 저장")
    created_at: datetime = Field(default_factory=datetime.now)
    
    # 관계 (논리 FK, 1:1)
    session_praat_result: Optional["SessionPraatResult"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "TrainSessionPraatFeedback.session_praat_result_id==foreign(SessionPraatResult.id)",
            "foreign_keys": "[TrainSessionPraatFeedback.session_praat_result_id]",
            "uselist": False,  # 1:1 관계
        }
    )
    
    ai_model: Optional["AIModel"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "TrainSessionPraatFeedback.ai_model_id==foreign(AIModel.id)",
            "foreign_keys": "[TrainSessionPraatFeedback.ai_model_id]",
        }
    )

