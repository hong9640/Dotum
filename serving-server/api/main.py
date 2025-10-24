from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from api.core.config import settings
from api.core.middleware import register_middlewares
from api.service.dto import LipVideoGenerationRequest, LipVideoGenerationResponse
from api.service.ai_service import ai_service
from api.utils.gcs_client import gcs_client

import time
import logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    debug=settings.DEBUG,
)

register_middlewares(app)

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    try:
        # GCS 연결 테스트
        files = gcs_client.list_files("models/")
        return {
            "status": "ok",
            "gcs_connected": True,
            "model_files_count": len(files)
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.post("/api/v1/lip-video")
async def generate_lip_video(req: LipVideoGenerationRequest):
    """음성/영상 변환 API"""
    start_time = time.time()
    
    try:
        logger.info(f"Starting lip video generation for text: {req.word}")
        
        # 1. TTS 오디오 생성
        logger.info("Step 1: Generating TTS audio...")
        tts_audio_path = await ai_service.generate_tts_audio(req.word, req.tts_lang)
        if not tts_audio_path:
            raise HTTPException(status_code=500, detail="Failed to generate TTS audio")
        
        # 2. FreeVC 음성 변환
        logger.info("Step 2: Running FreeVC inference...")
        # 사용자 영상에서 오디오 추출이 필요한 경우 여기서 처리
        # 현재는 user_video_gs를 src_audio로 사용
        freevc_output_path = await ai_service.run_freevc_inference(
            src_audio_path=req.user_video_gs,
            ref_audio_path=tts_audio_path,
            output_prefix=f"user_{int(time.time())}"
        )
        if not freevc_output_path:
            raise HTTPException(status_code=500, detail="Failed to run FreeVC inference")
        
        # 3. Wav2Lip 립싱크
        logger.info("Step 3: Running Wav2Lip inference...")
        wav2lip_output_path = await ai_service.run_wav2lip_inference(
            face_video_path=req.user_video_gs,
            audio_path=freevc_output_path,
            output_prefix=f"user_{int(time.time())}"
        )
        if not wav2lip_output_path:
            raise HTTPException(status_code=500, detail="Failed to run Wav2Lip inference")
        
        process_time_ms = (time.time() - start_time) * 1000
        
        logger.info(f"Lip video generation completed in {process_time_ms:.2f}ms")
        
        return LipVideoGenerationResponse(
            result_video_gs=wav2lip_output_path,
            process_time_ms=process_time_ms
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in lip video generation: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/v1/gcs/test")
async def test_gcs_connection():
    """GCS 연결 테스트 엔드포인트"""
    try:
        # 버킷 목록 조회
        files = gcs_client.list_files("")
        model_files = gcs_client.list_files("models/")
        
        return {
            "status": "success",
            "bucket": settings.GCS_BUCKET,
            "total_files": len(files),
            "model_files": len(model_files),
            "model_files_list": model_files[:10]  # 처음 10개만 반환
        }
    except Exception as e:
        logger.error(f"GCS test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
