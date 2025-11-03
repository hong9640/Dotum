from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from enum import Enum
from sqlalchemy.orm import foreign

if TYPE_CHECKING:
    from api.src.user.user_model import User


class MediaType(str, Enum):
    """미디어 파일 타입"""
    AUDIO = "audio"
    VIDEO = "video"
    IMAGE = "image"
    TRAIN = "train"


class MediaStatus(str, Enum):
    """미디어 파일 상태"""
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class MediaFile(SQLModel, table=True):
    """미디어 파일 모델"""
    __tablename__ = "media_files"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, description="사용자 ID (논리 FK)")
    object_key: str = Field(max_length=256, description="GCS 객체 키")
    media_type: MediaType = Field(description="미디어 타입")
    file_name: str = Field(max_length=255, description="파일명")
    file_size_bytes: int = Field(description="파일 크기 (바이트)")
    format: str = Field(max_length=50, description="파일 포맷")
    duration_ms: Optional[int] = Field(default=None, description="재생 시간 (밀리초)")
    width_px: Optional[int] = Field(default=None, description="너비 (픽셀)")
    height_px: Optional[int] = Field(default=None, description="높이 (픽셀)")
    status: MediaStatus = Field(default=MediaStatus.UPLOADED, description="처리 상태")
    is_public: Optional[bool] = Field(default=False, description="공개 여부")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    # 관계 (논리 FK)
    user: Optional["User"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "MediaFile.user_id==foreign(User.id)",
            "foreign_keys": "[MediaFile.user_id]",
        }
    )
