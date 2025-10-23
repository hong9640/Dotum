from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone, timedelta
from sqlmodel import Field, SQLModel, Relationship
from .user_enum import UserRoleEnum
if TYPE_CHECKING:
    from api.src.train.models import TrainResults

KST = timezone(timedelta(hours=9))

def get_current_kst_time():
    return datetime.now(KST)

class User(SQLModel, table=True):
    __tablename__ = "users"
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(max_length=30, nullable=False, unique=True) 
    password: str = Field(nullable=True)
    name: str = Field(max_length=10, nullable=False)
    phone_number: str = Field(max_length=12, nullable=False)
    role: UserRoleEnum = Field(nullable=False)
    gender: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=get_current_kst_time, nullable=False)
    updated_at: datetime = Field(default_factory=get_current_kst_time, nullable=True)
    deleted_at: Optional[datetime] = Field(default=None, nullable=True)

    # Realtionship(후에 다른 기능 추가되면 추가할 예정!)
    train_results: list["TrainResults"] = Relationship(back_populates="user")
    