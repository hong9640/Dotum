from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime
from typing import TYPE_CHECKING, Optional, List, Dict, Any
from enum import Enum
from sqlalchemy.orm import foreign
from sqlalchemy import Column, JSON


def get_current_datetime():
    """현재 시간을 00:00:00으로 설정"""
    now = datetime.now()
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


if TYPE_CHECKING:
    from .training_item import TrainingItem
    from user.user_model import User


class TrainingType(str, Enum):
    WORD = "word"
    SENTENCE = "sentence"

class TrainingSessionStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PAUSED = "paused"

class TrainingSession(SQLModel, table=True):
    __tablename__ = "training_sessions"
    
    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    session_name: str = Field(description="세션 이름")
    type: TrainingType = Field(description="훈련 타입")
    status: TrainingSessionStatus = Field(default=TrainingSessionStatus.IN_PROGRESS, description="세션 상태")
    training_date: datetime = Field(default_factory=get_current_datetime, description="훈련 날짜")
    
    # 진행 상황
    total_items: int = Field(description="총 아이템 수")
    completed_items: int = Field(default=0, description="완료된 아이템 수")
    current_item_index: int = Field(default=0, description="현재 진행 중인 아이템 인덱스")
    progress_percentage: float = Field(default=0.0, description="진행률 (0.0-1.0)")

    # 평균 점수
    average_score: Optional[float] = Field(default=0, description="평균 점수")

    # 세션 전체 피드백
    overall_feedback: Optional[str] = Field(default=None, description="세션 전체 피드백")
    
    # 메타데이터
    session_metadata: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON), description="추가 메타데이터")
    
    # 시간 정보
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = Field(default=None, description="시작 시간")
    completed_at: Optional[datetime] = Field(default=None, description="완료 시간")
    
    # Relationships (논리 FK)
    training_items: List["TrainingItem"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "TrainingSession.id==foreign(TrainingItem.training_session_id)",
            "foreign_keys": "[TrainingItem.training_session_id]",
        }
    )
    
    def update_progress(self):
        """진행률 자동 업데이트"""
        if self.total_items > 0:
            self.progress_percentage = self.completed_items / self.total_items
            self.updated_at = datetime.now()
    
    def can_start(self) -> bool:
        """세션 시작 가능 여부 (이미 시작된 상태이므로 항상 False)"""
        return False  # 세션 생성 시 바로 시작되므로 더 이상 필요 없음
    
    def can_complete(self) -> bool:
        """세션 완료 가능 여부"""
        return self.status == TrainingSessionStatus.IN_PROGRESS
    
    def is_completed(self) -> bool:
        """세션 완료 여부"""
        return self.status == TrainingSessionStatus.COMPLETED
