from typing import Optional
from pydantic import BaseModel, Field

# ---------- 요청 DTO ----------

class LipVideoGenerationRequest(BaseModel):
    """음성/영상 변환 요청"""
    user_video_gs: str = Field(..., description="사용자 발화 영상이 업로드된 GCS 경로")
    gen_audio_gs: str = Field(..., description="생성된 오디오가 업로드된 GCS 경로")
    output_video_gs: str = Field(..., description="생성된 영상을 업로드할 GCS 경로 (미리 지정된 경로)")
    word: Optional[str] = Field(None, description="발음할 단어/문장 텍스트 (FPS 자동 조정용)")
    target_fps: Optional[int] = Field(None, description="출력 영상의 프레임률 (미지정시 자동: 문장 15fps, 단어 18fps)", ge=15, le=60)

# ---------- 응답 DTO ----------

class LipVideoGenerationResponse(BaseModel):
    """변환 완료 후 응답"""
    success: bool = Field(..., description="처리 성공 여부")
    result_video_gs: str = Field(..., description="생성된 합성 영상의 GCS 경로")
    process_time_ms: float | None = Field(None, description="총 처리 시간 (ms)")

