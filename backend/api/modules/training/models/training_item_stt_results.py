from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime
from api.core.time_utils import now_kst

if TYPE_CHECKING:
    from api.modules.training.models.training_item import TrainingItem
    from api.modules.training.models.ai_model import AIModel


class TrainingItemSttResults(SQLModel, table=True):
    """STT 결과 저장 테이블"""
    __tablename__ = "training_item_stt_results"
    id: int = Field(default=None, primary_key=True)
    training_item_id: int = Field(index=True, description="훈련 아이템 id(논리 fk)")
    ai_model_id: int = Field(index=True, description="AI 모델 ID (논리 FK)")
    stt_result: str = Field(description="STT 결과")
    created_at: datetime = Field(default_factory=now_kst)

    # 관계 (논리 FK)
    training_item: Optional["TrainingItem"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "TrainingItemSttResults.training_item_id==foreign(TrainingItem.id)",
            "foreign_keys": "[TrainingItemSttResults.training_item_id]",
            "overlaps": "training_item"
        }
    )
    
    ai_model: Optional["AIModel"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "TrainingItemSttResults.ai_model_id==foreign(AIModel.id)",
            "foreign_keys": "[TrainingItemSttResults.ai_model_id]",
            "overlaps": "ai_model,ai_model",
        }
    )
