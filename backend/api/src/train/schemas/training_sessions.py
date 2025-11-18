from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from enum import Enum

from ..models.training_session import TrainingType, TrainingSessionStatus
from .training_items import TrainingItemResponse, CurrentItemResponse
from .media import MediaResponse
from api.src.train.schemas.praat import PraatFeaturesResponse


class TrainingSessionCreate(BaseModel):
    """연습 세션 생성 요청"""
    session_name: str = Field(..., description="세션 이름", min_length=1, max_length=100)
    type: TrainingType = Field(..., description="연습 타입")
    item_count: int = Field(..., description="연습할 아이템 개수", ge=1, le=50)
    training_date: Optional[date] = Field(None, description="연습 날짜")
    session_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="추가 메타데이터")
    
    @field_validator('item_count')
    @classmethod
    def validate_item_count(cls, v):
        if v < 1 or v > 50:
            raise ValueError('아이템 개수는 1-50개 사이여야 합니다')
        return v


class TrainingSessionUpdate(BaseModel):
    """연습 세션 수정 요청"""
    session_name: Optional[str] = Field(None, description="세션 이름", min_length=1, max_length=100)
    session_metadata: Optional[Dict[str, Any]] = Field(None, description="추가 메타데이터")


class TrainingSessionStatusUpdate(BaseModel):
    """연습 세션 상태 업데이트 요청"""
    status: TrainingSessionStatus = Field(..., description="새로운 상태")
    reason: Optional[str] = Field(None, description="상태 변경 사유", max_length=200)


class TrainingSessionResponse(BaseModel):
    """연습 세션 응답"""
    session_id: int = Field(description="세션 ID", serialization_alias=None)
    user_id: int
    session_name: str
    type: TrainingType
    status: TrainingSessionStatus
    training_date: datetime
    
    # 진행 상황
    total_items: int
    completed_items: int
    current_item_index: int
    progress_percentage: float

    # 평균 점수
    average_score: Optional[float] = None

    # 세션 전체 피드백
    overall_feedback: Optional[str] = None
    
    # 메타데이터
    session_metadata: Dict[str, Any]
    
    # 시간 정보
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # 연습 아이템들
    training_items: List[TrainingItemResponse] = Field(default_factory=list, description="연습 아이템 목록")
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, by_alias=False)


class ItemSubmissionResponse(BaseModel):
    """아이템 제출 응답 (업로드 + 완료 + 다음 아이템 정보)"""
    session: TrainingSessionResponse
    next_item: Optional[CurrentItemResponse] = None
    media: MediaResponse
    praat: Optional[PraatFeaturesResponse] = None
    video_url: str
    message: str = "연습 아이템이 완료되었습니다."

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class TrainingSessionListResponse(BaseModel):
    """연습 세션 목록 응답"""
    sessions: List[TrainingSessionResponse]
    total: int
    page: int
    size: int
    has_next: bool


class CalendarResponse(BaseModel):
    """달력 응답"""
    year: int
    month: int
    data: Dict[str, int] = Field(description="날짜별 세션 수")


class DailyTrainingResponse(BaseModel):
    """일별 연습 기록 응답"""
    date: str
    sessions: List[TrainingSessionResponse]
    total_sessions: int
    completed_sessions: int
    in_progress_sessions: int


class CreateSuccessResponse(BaseModel):
    """생성 성공 응답"""
    session_id: int
    message: str = "연습 세션이 성공적으로 생성되었습니다."


class TrainingSessionStats(BaseModel):
    """연습 세션 통계"""
    total_sessions: int
    completed_sessions: int
    in_progress_sessions: int
    pending_sessions: int
    paused_sessions: int
    cancelled_sessions: int
    
    # 타입별 통계
    word_sessions: int
    sentence_sessions: int
    
    # 진행률 통계
    average_progress: float
    completion_rate: float


class TrainingSessionFilter(BaseModel):
    """연습 세션 필터"""
    type: Optional[TrainingType] = None
    status: Optional[TrainingSessionStatus] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    min_progress: Optional[float] = Field(None, ge=0.0, le=1.0)
    max_progress: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v, info):
        if v and hasattr(info, 'data') and 'start_date' in info.data and info.data['start_date'] and v < info.data['start_date']:
            raise ValueError('종료일은 시작일보다 늦어야 합니다')
        return v
    
    @field_validator('max_progress')
    @classmethod
    def validate_progress_range(cls, v, info):
        if v and hasattr(info, 'data') and 'min_progress' in info.data and info.data['min_progress'] is not None and v < info.data['min_progress']:
            raise ValueError('최대 진행률은 최소 진행률보다 커야 합니다')
        return v


class TrainingSessionSearch(BaseModel):
    """연습 세션 검색"""
    query: Optional[str] = Field(None, description="검색어", max_length=100)
    filters: Optional[TrainingSessionFilter] = None
    sort_by: str = Field("created_at", description="정렬 기준")
    sort_order: str = Field("desc", description="정렬 순서 (asc/desc)")
    page: int = Field(1, ge=1, description="페이지 번호")
    size: int = Field(20, ge=1, le=100, description="페이지 크기")
    
    @field_validator('sort_by')
    @classmethod
    def validate_sort_by(cls, v):
        allowed_fields = ['created_at', 'updated_at', 'training_date', 'progress_percentage', 'session_name']
        if v not in allowed_fields:
            raise ValueError(f'정렬 기준은 {allowed_fields} 중 하나여야 합니다')
        return v
    
    @field_validator('sort_order')
    @classmethod
    def validate_sort_order(cls, v):
        if v not in ['asc', 'desc']:
            raise ValueError('정렬 순서는 asc 또는 desc여야 합니다')
        return v
