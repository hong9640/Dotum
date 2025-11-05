from typing import Optional
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
