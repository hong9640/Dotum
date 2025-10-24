from sqlmodel import Field, SQLModel
from datetime import datetime

class TrainSentences(SQLModel, table=True):
    __tablename__ = "train_sentences"
    id: int = Field(default=None, primary_key=True)
    sentence: str = Field(unique=True, index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
