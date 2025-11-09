from typing import Optional, List
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
    image_url: Optional[str] = Field(default=None, description="VOCAL 세션의 그래프 이미지 URL")

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
    avg_cpp: Optional[float] = None
    avg_csid: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class VocalItemPraatDetail(BaseModel):
    """VOCAL 아이템별 Praat 상세 지표"""
    item_index: int = Field(description="아이템 인덱스")
    item_id: int = Field(description="아이템 ID")
    praat_features: Optional[PraatFeaturesResponse] = Field(
        None, 
        description="Praat 분석 결과 (없으면 null)"
    )
    
    model_config = ConfigDict(from_attributes=True)


class VocalTrainingResultsSummary(BaseModel):
    """VOCAL 훈련 결과 요약 (평균)"""
    session_id: int = Field(description="세션 ID")
    session_name: str = Field(description="세션 이름")
    total_items: int = Field(description="전체 아이템 수")
    completed_items: int = Field(description="완료된 아이템 수")
    average_results: SessionPraatResultResponse = Field(
        description="평균 Praat 지표"
    )
    
    model_config = ConfigDict(from_attributes=True)


class VocalTrainingResultsDetail(BaseModel):
    """VOCAL 훈련 결과 상세 (아이템별)"""
    session_id: int = Field(description="세션 ID")
    session_name: str = Field(description="세션 이름")
    total_items: int = Field(description="전체 아이템 수")
    completed_items: int = Field(description="완료된 아이템 수")
    items: List[VocalItemPraatDetail] = Field(
        description="각 아이템별 Praat 분석 결과"
    )
    
    model_config = ConfigDict(from_attributes=True)
