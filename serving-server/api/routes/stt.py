"""
음성 인식(STT) API 라우터
"""

from fastapi import APIRouter, HTTPException
from api.service.dto import (
    STTRequest, 
    STTResponse, 
    STTBatchRequest, 
    STTBatchResponse
)
from api.service.stt import get_stt_service
from api.core.logger import logger, log_api_call, log_error

router = APIRouter()


@router.post("/api/v1/stt/transcribe", response_model=STTResponse)
@log_api_call
async def transcribe_audio(req: STTRequest):
    """
    단일 오디오 파일 음성 인식 API
    
    - GCS 또는 URL에서 오디오 파일을 읽어 텍스트로 변환
    - 1600+ 언어 지원 (Omnilingual ASR)
    - 언어 자동 감지 또는 수동 지정 가능
    
    **주의**: 현재 40초 이하의 오디오만 지원
    """
    try:
        # 입력 검증
        if not req.audio_gs and not req.audio_url:
            raise ValueError("Either audio_gs or audio_url must be provided")
        
        # STT 서비스 가져오기
        stt_service = get_stt_service(model_size=req.model_size)
        
        # 음성 인식 실행
        audio_source = req.audio_gs or req.audio_url
        is_gcs = bool(req.audio_gs)
        
        logger.info(f"Transcription request - Source: {audio_source}, Lang: {req.lang or 'kor_Hang'}, Model: {req.model_size}")
        
        result = await stt_service.transcribe_single(
            audio_source=audio_source,
            lang=req.lang,
            is_gcs=is_gcs
        )
        
        if not result["success"]:
            raise ValueError("Transcription failed")
        
        # 응답 반환
        return STTResponse(
            success=result["success"],
            transcription=result["transcription"],
            language=result["language"],
            process_time_ms=result["process_time_ms"]
        )
        
    except ValueError as e:
        log_error("Business logic error in STT", error=e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error("Unexpected error in STT transcription", error=e)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


