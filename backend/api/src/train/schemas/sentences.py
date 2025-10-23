from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

# Request Schemas
class TrainSentenceCreate(BaseModel):
    sentence: str


class TrainSentenceUpdate(BaseModel):
    sentence: str


# Response Schemas
class TrainSentenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    sentence: str
    created_at: datetime
    updated_at: datetime

