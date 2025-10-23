from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy.orm import foreign
from datetime import datetime
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .sentences import TrainSentences
    from .words import TrainWords
    from user.user_model import User


class WordTrainResults(SQLModel, table=True):
    __tablename__ = "word_train_results"
    id: int = Field(default=None, primary_key=True)
    name: str
    word_accuracy: float
    created_at: datetime = Field(default_factory=datetime.now)
    
    train_words_id: Optional[int] = Field(default=None)
    user_id: Optional[int] = Field(default=None)
    
    # 편의를 위한 relationship (단방향, back_populates 없음)
    train_word: Optional["TrainWords"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "TrainWords.id==foreign(WordTrainResults.train_words_id)",
        }
    )
    user: Optional["User"] = Relationship(
        back_populates="word_train_results",
        sa_relationship_kwargs={
            "primaryjoin": "User.id==foreign(WordTrainResults.user_id)",
        }
    )


class SentenceTrainResults(SQLModel, table=True):
    __tablename__ = "sentence_train_results"
    id: int = Field(default=None, primary_key=True)
    name: str
    word_accuracy: float
    created_at: datetime = Field(default_factory=datetime.now)
    
    # 논리적 FK만 (단방향 참조)
    train_sentences_id: Optional[int] = Field(default=None)
    user_id: Optional[int] = Field(default=None)
    
    # 편의를 위한 relationship (단방향, back_populates 없음)
    train_sentence: Optional["TrainSentences"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "TrainSentences.id==foreign(SentenceTrainResults.train_sentences_id)",
        }
    )
    user: Optional["User"] = Relationship(
        back_populates="sentence_train_results",
        sa_relationship_kwargs={
            "primaryjoin": "User.id==foreign(SentenceTrainResults.user_id)",
        }
    )