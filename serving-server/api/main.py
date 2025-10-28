from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from api.core.config import settings
from api.core.middleware import register_middlewares
from api.core.logger import logger, log_api_call, log_step, log_success, log_error
from api.service.dto import LipVideoGenerationRequest, LipVideoGenerationResponse
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
    """음성/영상 변환 API"""
    start_time = time.time()
    
    try:
        logger.info(f"Word: {req.word}, Video: {req.user_video_gs}, Output: {req.output_video_gs}")
        
        # 1. 영상에서 오디오 추출
        log_step("Extracting audio from video")
        extracted_audio_path = await ai_service.extract_audio_from_video(req.user_video_gs)
        if not extracted_audio_path:
            raise HTTPException(status_code=500, detail="Failed to extract audio from video")
        log_success("Audio extracted from video", path=extracted_audio_path)
        
        # 2. TTS 오디오 생성
        log_step("Generating TTS audio")
        tts_audio_path = await ai_service.generate_tts_audio(req.word, req.tts_lang)
        if not tts_audio_path:
            raise HTTPException(status_code=500, detail="Failed to generate TTS audio")
        log_success("TTS audio generated", path=tts_audio_path)
        
        # 3. FreeVC 음성 변환
        log_step("Running FreeVC inference")
        freevc_output_path = await ai_service.run_freevc_inference(
            src_audio_path=extracted_audio_path,
            ref_audio_path=tts_audio_path,
            output_prefix=f"user_{int(time.time())}"
        )
        if not freevc_output_path:
            raise HTTPException(status_code=500, detail="Failed to run FreeVC inference")
        log_success("FreeVC inference completed", path=freevc_output_path)
        
        # 임시 파일 정리
        if os.path.exists(extracted_audio_path):
            os.unlink(extracted_audio_path)
        
        # 4. Wav2Lip 립싱크
        log_step("Running Wav2Lip inference")
        wav2lip_output_path = await ai_service.run_wav2lip_inference(
            face_video_path=req.user_video_gs,
            audio_path=freevc_output_path,
            output_prefix=f"user_{int(time.time())}"
        )
        if not wav2lip_output_path:
            raise HTTPException(status_code=500, detail="Failed to run Wav2Lip inference")
        log_success("Wav2Lip inference completed", path=wav2lip_output_path)
        
        # 5. 결과 파일을 지정된 경로로 복사
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

@app.get("/api/v1/gcs/test")
async def test_gcs_connection():
    """GCS 연결 테스트 엔드포인트"""
    try:
        files = gcs_client.list_files("")
        freevc_files = gcs_client.list_files(f"{settings.FREEVC_MODEL_PATH}/")
        wav2lip_files = gcs_client.list_files(f"{settings.WAV2LIP_MODEL_PATH}/")
        total_model_files = len(freevc_files) + len(wav2lip_files)
        
        log_success("GCS connection test", bucket=settings.GCS_BUCKET, total_files=len(files))
        
        return {
            "status": "success",
            "bucket": settings.GCS_BUCKET,
            "total_files": len(files),
            "freevc_files": len(freevc_files),
            "wav2lip_files": len(wav2lip_files),
            "total_model_files": total_model_files,
            "freevc_files_list": freevc_files[:5],
            "wav2lip_files_list": wav2lip_files[:5]
        }
    except Exception as e:
        log_error("GCS test failed", error=e)
        raise HTTPException(status_code=500, detail=str(e))
