from pydantic import BaseModel, Field

# ---------- 요청 DTO ----------

class LipVideoGenerationRequest(BaseModel):
    """음성/영상 변환 요청"""
    word: str = Field(..., description="사용자 발화 단어")
    user_video_gs: str = Field(..., description="사용자 발화 영상이 업로드된 GCS 경로")
    output_video_gs: str = Field(..., description="생성된 영상을 업로드할 GCS 경로 (미리 지정된 경로)")
    tts_lang: str = Field("ko", description="TTS 언어 코드 (기본: 한국어)")

class GttsLipVideoRequest(BaseModel):
    """gTTS를 사용한 음성/영상 변환 요청"""
    text: str = Field(..., description="변환할 텍스트")
    ref_audio_gs: str = Field(..., description="참조 오디오 GCS 경로")
    face_image_gs: str = Field(..., description="얼굴 이미지 GCS 경로")
    tts_lang: str = Field("ko", description="TTS 언어 코드 (기본: 한국어)")

# ---------- 응답 DTO ----------

class LipVideoGenerationResponse(BaseModel):
    """변환 완료 후 응답"""
    success: bool = Field(..., description="처리 성공 여부")
    word: str = Field(..., description="사용자 발화 단어")
    result_video_gs: str = Field(..., description="생성된 합성 영상의 GCS 경로")
    process_time_ms: float | None = Field(None, description="총 처리 시간 (ms)")

class GttsLipVideoResponse(BaseModel):
    """gTTS 변환 완료 후 응답"""
    success: bool = Field(..., description="처리 성공 여부")
    text: str = Field(..., description="입력 텍스트")
    tts_audio_gs: str = Field(..., description="생성된 TTS 오디오 GCS 경로")
    freevc_audio_gs: str = Field(..., description="FreeVC 변환된 오디오 GCS 경로")
    result_video_gs: str = Field(..., description="최종 립싱크 영상 GCS 경로")
    process_time_ms: float | None = Field(None, description="총 처리 시간 (ms)")
