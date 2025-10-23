from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime
from typing import Optional

# Word Train Results Schemas
class WordTrainResultCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100, description="이름은 1자 이상이어야 합니다")
    word_accuracy: float = Field(ge=0.0, le=1.0, description="정확도는 0.0에서 1.0 사이여야 합니다")
    train_words_id: Optional[int] = None
    user_id: Optional[int] = None
    
    @field_validator('name')
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('이름은 공백만으로 이루어질 수 없습니다')
        return v.strip()


class WordTrainResultUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    word_accuracy: Optional[float] = Field(None, ge=0.0, le=1.0)
    train_words_id: Optional[int] = None
    user_id: Optional[int] = None
    
    @field_validator('name')
    @classmethod
    def name_must_not_be_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError('이름은 공백만으로 이루어질 수 없습니다')
        return v.strip() if v else None


class WordTrainResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    word_accuracy: float
    train_words_id: Optional[int]
    user_id: Optional[int]
    created_at: datetime


# Sentence Train Results Schemas
class SentenceTrainResultCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100, description="이름은 1자 이상이어야 합니다")
    word_accuracy: float = Field(ge=0.0, le=1.0, description="정확도는 0.0에서 1.0 사이여야 합니다")
    train_sentences_id: Optional[int] = None
    user_id: Optional[int] = None
    
    @field_validator('name')
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('이름은 공백만으로 이루어질 수 없습니다')
        return v.strip()


class SentenceTrainResultUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    word_accuracy: Optional[float] = Field(None, ge=0.0, le=1.0)
    train_sentences_id: Optional[int] = None
    user_id: Optional[int] = None
    
    @field_validator('name')
    @classmethod
    def name_must_not_be_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError('이름은 공백만으로 이루어질 수 없습니다')
        return v.strip() if v else None


class SentenceTrainResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    word_accuracy: float
    train_sentences_id: Optional[int]
    user_id: Optional[int]
    created_at: datetime

