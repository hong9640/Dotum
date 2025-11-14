from typing import Optional, List, Union, Dict
from pydantic import BaseModel, Field, ConfigDict

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

# ---------- STT 요청 DTO ----------

class STTRequest(BaseModel):
    """음성 인식 요청"""
    model_config = ConfigDict(protected_namespaces=())  # model_ 네임스페이스 경고 해제
    
    audio_gs: Optional[str] = Field(None, description="GCS에 업로드된 오디오 파일 경로")
    audio_url: Optional[str] = Field(None, description="공개 URL로 접근 가능한 오디오 파일 경로")
    lang: Optional[str] = Field("kor_Hang", description="언어 코드 (예: eng_Latn, kor_Hang). 미지정시 자동 감지")
    model_size: Optional[str] = Field("300M", description="모델 크기 (300M, 1B, 3B, 7B)")

class STTBatchRequest(BaseModel):
    """배치 음성 인식 요청"""
    model_config = ConfigDict(protected_namespaces=())  # model_ 네임스페이스 경고 해제
    
    audio_files: List[Union[str, Dict]] = Field(..., description="GCS 경로 또는 URL 리스트")
    langs: Optional[List[str]] = Field(None, description="각 오디오에 대한 언어 코드 리스트")
    model_size: Optional[str] = Field("7B", description="모델 크기 (300M, 1B, 3B, 7B)")
    batch_size: Optional[int] = Field(2, description="배치 처리 크기", ge=1, le=32)

# ---------- STT 응답 DTO ----------

class STTResponse(BaseModel):
    """음성 인식 응답"""
    success: bool = Field(..., description="처리 성공 여부")
    transcription: str = Field(..., description="인식된 텍스트")
    language: Optional[str] = Field(None, description="감지된 언어 코드")
    process_time_ms: float = Field(..., description="처리 시간 (ms)")

class STTBatchResponse(BaseModel):
    """배치 음성 인식 응답"""
    success: bool = Field(..., description="처리 성공 여부")
    transcriptions: List[str] = Field(..., description="인식된 텍스트 리스트")
    languages: Optional[List[str]] = Field(None, description="각 오디오의 언어 코드 리스트")
    process_time_ms: float = Field(..., description="총 처리 시간 (ms)")
