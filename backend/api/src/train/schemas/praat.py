from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class PraatFeaturesResponse(BaseModel):
    """Praat 분석 결과 응답 스키마"""
    praat_id: int = Field(description="Praat 분석 ID", alias="id")
    media_id: int
    jitter_local: Optional[float]
    shimmer_local: Optional[float]
    hnr: Optional[float]
    nhr: Optional[float]
    f0: Optional[float]
    max_f0: Optional[float]
    min_f0: Optional[float]
    cpp: Optional[float]
    csid: Optional[float]
    lh_ratio_mean_db: Optional[float]
    lh_ratio_sd_db: Optional[float]
    f1: Optional[float]
    f2: Optional[float]
    intensity_mean: Optional[float]

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class SessionPraatResultResponse(BaseModel):
    """세션 단위 Praat 평균 지표 응답 스키마"""
    avg_jitter_local: Optional[float] = None
    avg_shimmer_local: Optional[float] = None
    avg_hnr: Optional[float] = None
    avg_nhr: Optional[float] = None
    avg_lh_ratio_mean_db: Optional[float] = None
    avg_lh_ratio_sd_db: Optional[float] = None
    avg_max_f0: Optional[float] = None
    avg_min_f0: Optional[float] = None
    avg_intensity_mean: Optional[float] = None
    avg_f0: Optional[float] = None
    avg_f1: Optional[float] = None
    avg_f2: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
