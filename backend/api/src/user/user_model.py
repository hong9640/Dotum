from typing import Optional
from datetime import datetime, timezone, timedelta
from sqlmodel import Field, SQLModel
from .user_enum import UserRoleEnum

KST = timezone(timedelta(hours=9))

def get_current_kst_time():
    return datetime.now(KST)

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(max_length=30, nullable=False, unique=True) 
    password: str = Field(nullable=True)
    name: str = Field(max_length=10, nullable=False)
    phone_number: str = Field(max_length=12, nullable=False)
    role: UserRoleEnum = Field(nullable=False)
    gender: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=get_current_kst_time, nullable=False)
    updated_at: datetime = Field(default_factory=get_current_kst_time, nullable=True)

# Realtionship(후에 다른 기능 추가되면 추가할 예정!)