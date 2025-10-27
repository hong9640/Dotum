from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from api.core.config import settings
from api.core.middleware import register_middlewares
from api.core.logger import logger, log_api_call, log_step, log_success, log_error
from api.service.dto import LipVideoGenerationRequest, LipVideoGenerationResponse, GttsLipVideoRequest, GttsLipVideoResponse
from api.service.ai_service import ai_service
from api.utils.gcs_client import gcs_client

import time
import os

app = FastAPI(
    title=settings.PROJECT_NAME,
    debug=settings.DEBUG,
)

register_middlewares(app)

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    try:
        files = gcs_client.list_files("models/")
        log_success("Health check completed", files_count=len(files))
        return {
            "status": "ok",
            "gcs_connected": True,
            "model_files_count": len(files)
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
    """음성/영상 변환 API"""
    start_time = time.time()
    
    try:
        logger.info(f"Word: {req.word}, Video: {req.user_video_gs}, Output: {req.output_video_gs}")
        
        # 1. TTS 오디오 생성
        log_step("Generating TTS audio")
        tts_audio_path = await ai_service.generate_tts_audio(req.word, req.tts_lang)
        if not tts_audio_path:
            raise HTTPException(status_code=500, detail="Failed to generate TTS audio")
        log_success("TTS audio generated", path=tts_audio_path)
        
        # 2. FreeVC 음성 변환
        log_step("Running FreeVC inference")
        freevc_output_path = await ai_service.run_freevc_inference(
            src_audio_path=req.user_video_gs,
            ref_audio_path=tts_audio_path,
            output_prefix=f"user_{int(time.time())}"
        )
        if not freevc_output_path:
            raise HTTPException(status_code=500, detail="Failed to run FreeVC inference")
        log_success("FreeVC inference completed", path=freevc_output_path)
        
        # 3. Wav2Lip 립싱크
        log_step("Running Wav2Lip inference")
        wav2lip_output_path = await ai_service.run_wav2lip_inference(
            face_video_path=req.user_video_gs,
            audio_path=freevc_output_path,
            output_prefix=f"user_{int(time.time())}"
        )
        if not wav2lip_output_path:
            raise HTTPException(status_code=500, detail="Failed to run Wav2Lip inference")
        log_success("Wav2Lip inference completed", path=wav2lip_output_path)
        
        # 4. 결과 파일을 지정된 경로로 복사
        log_step("Copying result to specified path", details=req.output_video_gs)
        if not gcs_client.download_file(wav2lip_output_path, "/tmp/result_temp.mp4"):
            raise HTTPException(status_code=500, detail="Failed to download result file")
        
        if not gcs_client.upload_file("/tmp/result_temp.mp4", req.output_video_gs):
            raise HTTPException(status_code=500, detail="Failed to upload to specified path")
        
        # 임시 파일 정리
        if os.path.exists("/tmp/result_temp.mp4"):
            os.unlink("/tmp/result_temp.mp4")
        
        process_time_ms = (time.time() - start_time) * 1000
        
        return LipVideoGenerationResponse(
            success=True,
            word=req.word,
            result_video_gs=req.output_video_gs,
            process_time_ms=process_time_ms
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error("Unexpected error in lip video generation", error=e)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/api/v1/gtts-lip-video")
@log_api_call
async def generate_gtts_lip_video(req: GttsLipVideoRequest):
    """gTTS를 사용한 음성/영상 변환 API"""
    start_time = time.time()
    
    try:
        logger.info(f"Text: {req.text[:50]}..., Ref: {req.ref_audio_gs}, Face: {req.face_image_gs}")
        
        # gTTS 워크플로우 실행
        result = await ai_service.process_lip_video_gtts(
            text=req.text,
            ref_audio_path=req.ref_audio_gs,
            face_image_path=req.face_image_gs,
            output_prefix=f"gtts_{int(time.time())}"
        )
        
        if not result or not result.get("success"):
            raise HTTPException(status_code=500, detail="Failed to process gTTS workflow")
        
        process_time_ms = (time.time() - start_time) * 1000
        
        return GttsLipVideoResponse(
            success=True,
            text=result["text"],
            tts_audio_gs=result["tts_audio_path"],
            freevc_audio_gs=result["freevc_audio_path"],
            result_video_gs=result["final_video_path"],
            process_time_ms=process_time_ms
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error("Unexpected error in gTTS lip video generation", error=e)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/v1/gcs/test")
async def test_gcs_connection():
    """GCS 연결 테스트 엔드포인트"""
    try:
        files = gcs_client.list_files("")
        model_files = gcs_client.list_files("models/")
        
        log_success("GCS connection test", bucket=settings.GCS_BUCKET, total_files=len(files))
        
        return {
            "status": "success",
            "bucket": settings.GCS_BUCKET,
            "total_files": len(files),
            "model_files": len(model_files),
            "model_files_list": model_files[:10]
        }
    except Exception as e:
        log_error("GCS test failed", error=e)
        raise HTTPException(status_code=500, detail=str(e))
