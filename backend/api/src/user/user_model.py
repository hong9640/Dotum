from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone, timedelta
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy.orm import foreign
from .user_enum import UserRoleEnum
if TYPE_CHECKING:
    from api.src.train.models import TrainingSession
    from api.src.train.models.media import MediaFile

class User(SQLModel, table=True):
    __tablename__ = "users"
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(max_length=30, nullable=False, unique=True) 
    password: str = Field(nullable=True)
    name: str = Field(max_length=10, nullable=False)
    phone_number: str = Field(max_length=30, nullable=False)
    role: UserRoleEnum = Field(nullable=False)
    gender: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now, nullable=True)
    deleted_at: Optional[datetime] = Field(default=None, nullable=True)

    # 통합 훈련 세션
    training_sessions: list["TrainingSession"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "User.id==foreign(TrainingSession.user_id)",
            "foreign_keys": "[TrainingSession.user_id]",
        }
    )
    
    # 미디어 파일
    media_files: list["MediaFile"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "User.id==foreign(MediaFile.user_id)",
            "foreign_keys": "[MediaFile.user_id]",
        }
    )
    