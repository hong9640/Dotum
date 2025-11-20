from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy.orm import foreign
from api.core.time_utils import now_kst

if TYPE_CHECKING:
    from api.modules.training.models.training_session import TrainingSession


class SessionPraatResult(SQLModel, table=True):
    """훈련 세션 단위 Praat 평균 지표 저장 (vocal 타입 전용)"""
    __tablename__ = "session_praat_results"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    training_session_id: int = Field(index=True, description="훈련 세션 ID (논리 FK)")
    
    # Praat 평균 지표 (모두 nullable)
    # 첫 번째 그룹 (0 ~ n-1): jitter_local, shimmer_local, nhr, hnr, lh_ratio_mean_db, lh_ratio_sd_db
    avg_jitter_local: Optional[float] = None
    avg_shimmer_local: Optional[float] = None
    avg_nhr: Optional[float] = None
    avg_hnr: Optional[float] = None
    avg_lh_ratio_mean_db: Optional[float] = None
    avg_lh_ratio_sd_db: Optional[float] = None
    
    # 두 번째 그룹 (n ~ 5n-1): max_f0, min_f0, intensity_mean
    avg_max_f0: Optional[float] = None
    avg_min_f0: Optional[float] = None
    avg_intensity_mean: Optional[float] = None
    
    # 전체 (0 ~ 5n-1): f0, f1, f2
    avg_f0: Optional[float] = None
    avg_f1: Optional[float] = None
    avg_f2: Optional[float] = None

    # cpp, csid 평균
    avg_cpp: Optional[float] = None
    avg_csid: Optional[float] = None
    
    created_at: datetime = Field(default_factory=now_kst)
    updated_at: datetime = Field(default_factory=now_kst)
    
    # 관계 (논리 FK)
    training_session: Optional["TrainingSession"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "SessionPraatResult.training_session_id==foreign(TrainingSession.id)",
            "foreign_keys": "[SessionPraatResult.training_session_id]",
        }
    )

