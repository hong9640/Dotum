from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy.orm import foreign
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .sentences import TrainSentences


class TrainWords(SQLModel, table=True):
    __tablename__ = "train_words"
    id: int = Field(default=None, primary_key=True)
    word: str = Field(unique=True, index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    #역참조 관계
    train_sentences: list["TrainSentences"] = Relationship(
        back_populates="train_word",
        sa_relationship_kwargs={
            "primaryjoin": "TrainWords.id==foreign(TrainSentences.train_words_id)",
        }
    )
