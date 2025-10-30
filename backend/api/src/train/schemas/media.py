from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from ..models.media import MediaType, MediaStatus


class MediaCreate(BaseModel):
    """미디어 파일 생성 스키마"""
    object_key: str = Field(..., max_length=256, description="GCS 객체 키")
    media_type: MediaType = Field(..., description="미디어 타입")
    file_name: str = Field(..., max_length=255, description="파일명")
    file_size_bytes: int = Field(..., gt=0, description="파일 크기 (바이트)")
    format: str = Field(..., max_length=50, description="파일 포맷")
    duration_ms: Optional[int] = Field(None, ge=0, description="재생 시간 (밀리초)")
    width_px: Optional[int] = Field(None, ge=0, description="너비 (픽셀)")
    height_px: Optional[int] = Field(None, ge=0, description="높이 (픽셀)")
    is_public: Optional[bool] = Field(False, description="공개 여부")


class MediaResponse(BaseModel):
    """미디어 파일 응답 스키마"""
    media_id: int = Field(description="미디어 파일 ID")
    user_id: int
    object_key: str
    media_type: MediaType
    file_name: str
    file_size_bytes: int
    format: str
    duration_ms: Optional[int]
    width_px: Optional[int]
    height_px: Optional[int]
    status: MediaStatus
    is_public: Optional[bool]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True, populate_by_name=False)


class MediaUpdate(BaseModel):
    """미디어 파일 업데이트 스키마"""
    status: Optional[MediaStatus] = None
    duration_ms: Optional[int] = Field(None, ge=0)
    width_px: Optional[int] = Field(None, ge=0)
    height_px: Optional[int] = Field(None, ge=0)
    is_public: Optional[bool] = None


class MediaListResponse(BaseModel):
    """미디어 파일 목록 응답 스키마"""
    media_id: int = Field(description="미디어 파일 ID")
    object_key: str
    media_type: MediaType
    file_name: str
    file_size_bytes: int
    format: str
    duration_ms: Optional[int]
    width_px: Optional[int]
    height_px: Optional[int]
    status: MediaStatus
    is_public: Optional[bool]
    created_at: Optional[datetime]
    signed_url: Optional[str] = Field(None, description="동영상 시청용 서명된 URL")

    model_config = ConfigDict(from_attributes=True, populate_by_name=False)


class MediaUploadUrlResponse(BaseModel):
    """미디어 파일 업로드 URL 응답 스키마"""
    upload_url: str = Field(..., description="업로드용 서명된 URL")
    media_file_id: int = Field(..., description="미디어 파일 ID")
    expires_in: int = Field(..., description="URL 만료 시간 (초)")


class MediaProgressResponse(BaseModel):
    """미디어 파일 업로드 진행 상황 응답 스키마"""
    media_file_id: int
    status: MediaStatus
    progress_percentage: Optional[float] = Field(None, ge=0, le=100)
    estimated_completion_time: Optional[datetime]


class MediaFilter(BaseModel):
    """미디어 파일 필터 스키마"""
    media_type: Optional[MediaType] = None
    status: Optional[MediaStatus] = None
    is_public: Optional[bool] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
