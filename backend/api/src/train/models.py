from sqlmodel import Field, SQLModel, Relationship, Session, select
from datetime import datetime
from typing import Optional


class TrainResults(SQLModel, table=True):
    __tablename__ = "train_results"
    id: int = Field(default=None, primary_key=True)
    name: str
    word_accuracy: float
    created_at: datetime = Field(default_factory=datetime.now)
    train_sentences_id: int
    train_sentence: "TrainSentences" = Relationship(back_populates="train_results")

class TrainWords(SQLModel, table=True):
    __tablename__ = "train_words"
    id: int = Field(default=None, primary_key=True)
    word: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # 1:N 관계 - 하나의 단어가 여러 문장에 사용될 수 있음
    train_sentences: list["TrainSentences"] = Relationship(back_populates="train_word")

    
class TrainSentences(SQLModel, table=True):
    __tablename__ = "train_sentences"
    id: int = Field(default=None, primary_key=True)
    sentence: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # N:1 관계 - 여러 문장이 하나의 단어에 속함
    train_words_id: int
    train_word: "TrainWords" = Relationship(back_populates="train_sentences")
    
    # 1:N 관계 - 하나의 문장이 여러 결과를 가질 수 있음
    train_results: list["TrainResults"] = Relationship(back_populates="train_sentence")