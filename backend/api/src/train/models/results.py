from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy.orm import foreign
from datetime import datetime
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .sentences import TrainSentences


class TrainResults(SQLModel, table=True):
    __tablename__ = "train_results"
    id: int = Field(default=None, primary_key=True)
    name: str
    word_accuracy: float
    created_at: datetime = Field(default_factory=datetime.now)
    train_sentences_id: Optional[int] = Field(default=None)
    train_sentence: Optional["TrainSentences"] = Relationship(
        back_populates="train_results",
        sa_relationship_kwargs={
            "primaryjoin": "TrainSentences.id==foreign(TrainResults.train_sentences_id)",
        }
    )