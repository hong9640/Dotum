from fastapi import FastAPI
from fastapi.responses import JSONResponse

from api.core.config import settings
from api.core.middleware import register_middlewares
from api.core.logger import logger, log_success, log_error

import os

# 포트에 따라 다른 라우터 로드
PORT = int(os.environ.get("PORT", 8000))

app = FastAPI(
    title=settings.PROJECT_NAME,
    debug=settings.DEBUG,
)

register_middlewares(app)

# 포트별 라우터 로드
if PORT == 8000:
    # Wav2Lip 서버 (8000 포트)
    try:
        from api.routes.lip_video import router as lip_video_router
        app.include_router(lip_video_router)
        logger.info("Wav2Lip 서버 모드로 시작 (포트 8000) - Lip video router loaded")
    except Exception as e:
        logger.warning(f"Failed to load lip video router: {e}")
        
elif PORT == 8080:
    # STT 서버 (8080 포트)
    try:
        from api.routes.stt import router as stt_router
        app.include_router(stt_router)
        logger.info("STT 서버 모드로 시작 (포트 8080) - STT router loaded")
    except Exception as e:
        logger.warning(f"Failed to load STT router: {e}")
else:
    logger.warning(f"Unknown port {PORT}, no routers loaded. Use PORT=8000 for Wav2Lip or PORT=8080 for STT")

@app.get("/")
def endpoint_check():
    return {"server_status": "running", "port": PORT, "mode": "wav2lip" if PORT == 8000 else "stt" if PORT == 8080 else "unknown"}

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    try:
        if PORT == 8000:
            # Wav2Lip 서버의 경우 모델 파일 존재 확인
            wav2lip_model_path = os.path.join(settings.LOCAL_WAV2LIP_PATH, "checkpoints", "wav2lip_gan.pth")
            wav2lip_model_exists = os.path.exists(wav2lip_model_path)
            
            log_success("Health check completed", wav2lip_model=wav2lip_model_exists)
            return {
                "status": "ok" if wav2lip_model_exists else "warning",
                "port": PORT,
                "mode": "wav2lip",
                "models_ready": wav2lip_model_exists,
                "wav2lip_model_exists": wav2lip_model_exists
            }
        elif PORT == 8080:
            # STT 서버의 경우 기본 헬스 체크
            log_success("Health check completed", mode="stt")
            return {
                "status": "ok",
                "port": PORT,
                "mode": "stt"
            }
        else:
            return {
                "status": "warning",
                "port": PORT,
                "mode": "unknown",
                "message": "Unknown port configuration"
            }
    except Exception as e:
        log_error("Health check failed", error=e)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e), "port": PORT}
        )