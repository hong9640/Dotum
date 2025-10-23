from pydantic import BaseModel, ConfigDict
from datetime import datetime

# Request Schemas
class TrainWordCreate(BaseModel):
    word: str

class TrainWordUpdate(BaseModel):
    word: str

# Response Schemas
class TrainWordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    word: str
    created_at: datetime
    updated_at: datetime
