from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime
from typing import Optional

# Request Schemas
class TrainSentenceCreate(BaseModel):
    sentence: str = Field(min_length=4, max_length=200, description="문장은 4글자 이상 200글자 이하 이어야 합니다")
    
    @field_validator('sentence')
    @classmethod
    def sentence_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('문장은 공백만으로 이루어질 수 없습니다')
        return v.strip()

    
class TrainSentenceUpdate(BaseModel):
    sentence: str = Field(min_length=4, max_length=200, description="문장은 4글자 이상 200글자 이하 이어야 합니다")
    
    @field_validator('sentence')
    @classmethod
    def sentence_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('문장은 공백만으로 이루어질 수 없습니다')
        return v.strip()


# Response Schemas
class TrainSentenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    sentence: str
    created_at: datetime
    updated_at: datetime

