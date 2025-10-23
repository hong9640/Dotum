from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy.orm import foreign
from datetime import datetime
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .words import TrainWords
    from .results import TrainResults


class TrainSentences(SQLModel, table=True):
    __tablename__ = "train_sentences"
    id: int = Field(default=None, primary_key=True)
    sentence: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    #정참조 관계
    train_words_id: Optional[int] = Field(default=None)
    train_word: Optional["TrainWords"] = Relationship(
        back_populates="train_sentences",
        sa_relationship_kwargs={
            "primaryjoin": "TrainWords.id==foreign(TrainSentences.train_words_id)",
        }
    )
    
    #역참조 관계
    train_results: list["TrainResults"] = Relationship(
        back_populates="train_sentence",
        sa_relationship_kwargs={
            "primaryjoin": "TrainSentences.id==foreign(TrainResults.train_sentences_id)",
        }
    )
