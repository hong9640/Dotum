from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy.orm import foreign
from datetime import datetime
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .sentences import TrainSentences
    from .training_item import TrainingItem


class TrainWords(SQLModel, table=True):
    __tablename__ = "train_words"
    id: int = Field(default=None, primary_key=True)
    word: str = Field(unique=True, index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Relationships (논리 FK)
    training_items: List["TrainingItem"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "TrainWords.id==foreign(TrainingItem.word_id)",
            "foreign_keys": "[TrainingItem.word_id]",
        }
    )