from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy.orm import foreign
from datetime import datetime
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .training_item import TrainingItem


class TrainSentences(SQLModel, table=True):
    __tablename__ = "train_sentences"
    id: int = Field(default=None, primary_key=True)
    sentence: str = Field(unique=True, index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Relationships (논리 FK)
    training_items: List["TrainingItem"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "TrainSentences.id==foreign(TrainingItem.sentence_id)",
            "foreign_keys": "[TrainingItem.sentence_id]",
        }
    )
    
