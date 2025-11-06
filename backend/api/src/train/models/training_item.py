from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy.orm import foreign


def get_current_datetime():
    """현재 시간을 00:00:00으로 설정"""
    now = datetime.now()
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


if TYPE_CHECKING:
    from .training_session import TrainingSession
    from .words import TrainWords
    from .sentences import TrainSentences
    from .media import MediaFile


class TrainingItem(SQLModel, table=True):
    __tablename__ = "training_items"
    
    id: int = Field(default=None, primary_key=True)
    training_session_id: int = Field(index=True)
    item_index: int = Field(description="아이템 순서 (0부터 시작)")
    word_id: Optional[int] = Field(default=None, description="단어 ID (단어 훈련인 경우)")
    sentence_id: Optional[int] = Field(default=None, description="문장 ID (문장 훈련인 경우)")
    is_completed: bool = Field(default=False, description="완료 여부")
    score: Optional[float] = Field(default=None, description="점수")
    feedback: Optional[str] = Field(default=None, description="피드백")
    video_url: Optional[str] = Field(default=None, description="업로드된 동영상 URL")
    media_file_id: Optional[int] = Field(default=None, description="미디어 파일 ID")
    completed_at: Optional[datetime] = Field(default=None, description="완료 시간")
    created_at: datetime = Field(default_factory=get_current_datetime)
    updated_at: datetime = Field(default_factory=get_current_datetime)
    
    # Relationships (논리 FK)
    # training_session은 backref로 자동 생성됨
    word: Optional["TrainWords"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "TrainingItem.word_id==foreign(TrainWords.id)",
            "foreign_keys": "[TrainingItem.word_id]",
        }
    )
    sentence: Optional["TrainSentences"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "TrainingItem.sentence_id==foreign(TrainSentences.id)",
            "foreign_keys": "[TrainingItem.sentence_id]",
        }
    )
    media_file: Optional["MediaFile"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "TrainingItem.media_file_id==foreign(MediaFile.id)",
            "foreign_keys": "[TrainingItem.media_file_id]",
            "overlaps": "media_file"
        }
    )
