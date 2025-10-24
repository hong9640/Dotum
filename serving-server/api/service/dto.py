from pydantic import BaseModel, Field

# ---------- 요청 DTO ----------

class LipVideoGenerationRequest(BaseModel):
    """음성/영상 변환 요청"""
    user_video_gs: str = Field(..., description="GCS 경로: gs://bucket/user_raw/...mp4")
    word: str = Field(..., description="발화한 단어 (TTS 기준)")
    tts_lang: str = Field("ko", description="TTS 언어 코드 (기본: 한국어)")

# ---------- 응답 DTO ----------

class LipVideoGenerationResponse(BaseModel):
    """변환 완료 후 응답"""
    result_video_gs: str = Field(..., description="생성된 합성 영상의 GCS 경로")
    process_time_ms: float | None = Field(None, description="총 처리 시간 (ms)")
