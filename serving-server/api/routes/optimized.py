"""
최적화 버전 테스트용 라우터
"""

from fastapi import APIRouter, HTTPException
from api.service.dto import LipVideoGenerationRequest, LipVideoGenerationResponse
from api.service.ai_service_optimized import ai_service_optimized
from api.core.logger import logger, log_api_call, log_error

router = APIRouter()


@router.post("/api/v1/lip-video-optimized")
@log_api_call
async def generate_lip_video_optimized(req: LipVideoGenerationRequest):
    """
    음성/영상 변환 API (최적화 버전)
    - 모델 사전 로드
    - subprocess 제거
    - 직접 추론 실행
    """
    try:
        logger.info(f"Request received [OPTIMIZED] - Word: {req.word}, Video: {req.user_video_gs}")
        
        # 최적화된 AI 서비스 파이프라인 실행
        result = await ai_service_optimized.process_lip_video_pipeline(
            user_video_gs=req.user_video_gs,
            word=req.word,
            output_video_gs=req.output_video_gs,
            tts_lang=req.tts_lang
        )
        
        # 응답 반환
        return LipVideoGenerationResponse(
            success=result["success"],
            word=req.word,
            result_video_gs=result["result_video_gs"],
            process_time_ms=result["process_time_ms"]
        )
        
    except ValueError as e:
        log_error("Business logic error (optimized)", error=e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error("Unexpected error in optimized lip video generation", error=e)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/api/v1/preload-models")
async def preload_models():
    """
    모델 사전 로드 엔드포인트
    - 첫 요청 전에 호출하여 모델을 미리 로드
    """
    try:
        logger.info("Preloading models...")
        ai_service_optimized.ensure_models_loaded()
        logger.info("Models preloaded successfully")
        return {"status": "ok", "message": "Models preloaded successfully"}
    except Exception as e:
        log_error("Failed to preload models", error=e)
        raise HTTPException(status_code=500, detail=f"Failed to preload models: {str(e)}")

