from fastapi import FastAPI
from fastapi.responses import JSONResponse

from api.core.config import settings
from api.core.middleware import register_middlewares
from api.core.logger import logger, log_success, log_error

import os

app = FastAPI(
    title=settings.PROJECT_NAME,
    debug=settings.DEBUG,
)

register_middlewares(app)

# 립싱크 API 라우터 추가
try:
    from api.routes.lip_video import router as lip_video_router
    app.include_router(lip_video_router)
    logger.info("Lip video router loaded successfully")
except Exception as e:
    logger.warning(f"Failed to load lip video router: {e}")

# STT API 라우터 추가
try:
    from api.routes.stt import router as stt_router
    app.include_router(stt_router)
    logger.info("STT router loaded successfully")
except Exception as e:
    logger.warning(f"Failed to load STT router: {e}")

@app.get("/")
def endpoint_check():
  return ({"server_staus": "running"})

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    try:
        # Wav2Lip 모델 파일 존재 확인
        wav2lip_model_path = os.path.join(settings.LOCAL_WAV2LIP_PATH, "checkpoints", "Wav2Lip_gan.pth")
        wav2lip_model_exists = os.path.exists(wav2lip_model_path)
        
        log_success("Health check completed", wav2lip_model=wav2lip_model_exists)
        return {
            "status": "ok" if wav2lip_model_exists else "warning",
            "models_ready": wav2lip_model_exists,
            "wav2lip_model_exists": wav2lip_model_exists
        }
    except Exception as e:
        log_error("Health check failed", error=e)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )