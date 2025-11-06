from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from api.src.user.user_model import User

class RefreshToken(SQLModel, table=True):
    __tablename__ = "refresh_tokens"
    id: int | None = Field(default=None, primary_key=True)
    token_hash: str = Field(index=True, unique=True, nullable=False)
    expires_at: datetime = Field(nullable=False)
    user_id: int = Field(index=True, description="사용자 ID (논리 FK)")
    
    # 관계 (논리 FK)
    user: Optional["User"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "RefreshToken.user_id==foreign(User.id)", 
            "foreign_keys": "[RefreshToken.user_id]",
            "overlaps": "user"
        }
    )