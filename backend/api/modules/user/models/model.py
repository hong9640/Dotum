from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone, timedelta
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy.orm import foreign
from .enum import UserRoleEnum
if TYPE_CHECKING:
    from api.modules.training.models import TrainingSession
    from api.modules.training.models.media import MediaFile
    from api.modules.auth.models.token import RefreshToken

class UserVoice(SQLModel, table=True):
    __tablename__ = "user_voice"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(unique=True, index=True, description="사용자 ID (논리 FK)")
    
    voice_id: str = Field(index=True, description="ElevenLabs Voice ID")
    update_count: int = Field(default=0, description="Voice ID 갱신 횟수")
    source_audio_duration_ms: int = Field(default=0, description="Voice ID 생성에 사용된 원본 음성의 길이 (ms)")
    
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False, sa_column_kwargs={"onupdate": datetime.utcnow})


class User(SQLModel, table=True):
    __tablename__ = "users"
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(max_length=30, nullable=False, unique=True) 
    password: str = Field(nullable=True)
    name: str = Field(max_length=10, nullable=True)
    role: UserRoleEnum = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now, nullable=True)
    deleted_at: Optional[datetime] = Field(default=None, nullable=True)

    # 통합 연습 세션
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

    # 리프레시 토큰
    refresh_tokens: list["RefreshToken"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "User.id==foreign(RefreshToken.user_id)",
            "foreign_keys": "[RefreshToken.user_id]",
        }
    )

    # 사용자 목소리 (1:1 관계)
    voice: Optional["UserVoice"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "User.id==foreign(UserVoice.user_id)",
            "foreign_keys": "[UserVoice.user_id]",
            "uselist": False, # 1:1 관계 명시
        }
    )
    