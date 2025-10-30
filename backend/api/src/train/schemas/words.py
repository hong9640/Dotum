from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime

# Request Schemas
class TrainWordCreate(BaseModel):
    word: str = Field(min_length=1, max_length=20, description="단어는 1글자 이상 20글자 이하 이어야 합니다")
    
    @field_validator('word')
    @classmethod
    def word_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('단어는 공백만으로 이루어질 수 없습니다')
        return v.strip()

class TrainWordUpdate(BaseModel):
    word: str = Field(min_length=1, max_length=20, description="단어는 1글자 이상 20글자 이하 이어야 합니다")
    
    @field_validator('word')
    @classmethod
    def word_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('단어는 공백만으로 이루어질 수 없습니다')
        return v.strip()

# Response Schemas
class TrainWordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=False)
    
    word_id: int = Field(description="단어 ID")
    word: str
    created_at: datetime
    updated_at: datetime
