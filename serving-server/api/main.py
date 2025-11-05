from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from api.core.config import settings
from api.core.middleware import register_middlewares
from api.core.logger import logger, log_api_call, log_success, log_error
from api.service.dto import LipVideoGenerationRequest, LipVideoGenerationResponse
from api.service.ai_service import ai_service

import os

app = FastAPI(
    title=settings.PROJECT_NAME,
    debug=settings.DEBUG,
)

register_middlewares(app)

# 최적화 버전 라우터 추가 (테스트용)
try:
    from api.routes.optimized import router as optimized_router
    app.include_router(optimized_router)
    logger.info("Optimized router loaded successfully")
except Exception as e:
    logger.warning(f"Failed to load optimized router: {e}")

@app.get("/")
def endpoint_check():
  return ({"server_staus": "running"})

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    try:
        # 로컬 모델 파일 존재 확인
        freevc_model_path = os.path.join(settings.LOCAL_FREEVC_PATH, "checkpoints", "freevc-s.pth")
        freevc_config_path = os.path.join(settings.LOCAL_FREEVC_PATH, "configs", "freevc-s.json")
        wav2lip_model_path = os.path.join(settings.LOCAL_WAV2LIP_PATH, "checkpoints", "Wav2Lip_gan.pth")
        
        freevc_model_exists = os.path.exists(freevc_model_path)
        freevc_config_exists = os.path.exists(freevc_config_path)
        wav2lip_model_exists = os.path.exists(wav2lip_model_path)
        
        models_ready = freevc_model_exists and freevc_config_exists and wav2lip_model_exists
        
        log_success("Health check completed", 
                   freevc_model=freevc_model_exists,
                   freevc_config=freevc_config_exists,
                   wav2lip_model=wav2lip_model_exists)
        return {
            "status": "ok" if models_ready else "warning",
            "models_ready": models_ready,
            "freevc_model_exists": freevc_model_exists,
            "freevc_config_exists": freevc_config_exists,
            "wav2lip_model_exists": wav2lip_model_exists
        }
    except Exception as e:
        log_error("Health check failed", error=e)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.post("/api/v1/lip-video")
@log_api_call
async def generate_lip_video(req: LipVideoGenerationRequest):
    """음성/영상 변환 API - 사용자 영상을 기반으로 립싱크 영상 생성"""
    try:
        logger.info(f"Request received - Word: {req.word}, Video: {req.user_video_gs}, Output: {req.output_video_gs}")
        
        # AI 서비스 파이프라인 실행
        result = await ai_service.process_lip_video_pipeline(
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
        # 비즈니스 로직 에러
        log_error("Business logic error", error=e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # 예상치 못한 에러
        log_error("Unexpected error in lip video generation", error=e)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")