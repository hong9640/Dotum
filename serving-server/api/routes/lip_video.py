"""
립싱크 영상 생성 API 라우터
"""

from fastapi import APIRouter, HTTPException
from api.service.dto import LipVideoGenerationRequest, LipVideoGenerationResponse
from api.service.ai_service import ai_service
from api.core.logger import logger, log_api_call, log_error

router = APIRouter()


@router.post("/api/v1/lip-video")
@log_api_call
async def generate_lip_video(req: LipVideoGenerationRequest):
    """
    립싱크 영상 생성 API
    - 사용자 영상과 생성된 오디오를 GCS에서 다운로드
    - Wav2Lip으로 립싱크 합성
    - 결과 영상을 GCS에 업로드
    """
    try:
        logger.info(f"Request received - Video: {req.user_video_gs}, Audio: {req.gen_audio_gs}, Text: {req.word}")
        
        # 🎓 음성장애인 학습용: 자동 FPS 조정
        # target_fps가 지정되지 않았다면 텍스트 길이로 자동 결정
        if req.target_fps is None:
            if req.word:
                # 공백 포함 10자 이상이면 문장으로 간주
                is_sentence = len(req.word) >= 10
                target_fps = 15 if is_sentence else 18
                logger.info(f"Auto FPS: {'Sentence' if is_sentence else 'Word'} detected, using {target_fps}fps")
            else:
                target_fps = 18  # 기본값
                logger.info(f"No text provided, using default {target_fps}fps")
        else:
            target_fps = req.target_fps
            logger.info(f"Using specified FPS: {target_fps}fps")
        
        # AI 서비스 파이프라인 실행
        result = await ai_service.process_lip_video_pipeline(
            user_video_gs=req.user_video_gs,
            gen_audio_gs=req.gen_audio_gs,
            output_video_gs=req.output_video_gs,
            target_fps=target_fps
        )
        
        # 응답 반환
        return LipVideoGenerationResponse(
            success=result["success"],
            result_video_gs=result["result_video_gs"],
            process_time_ms=result["process_time_ms"]
        )
        
    except ValueError as e:
        log_error("Business logic error", error=e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error("Unexpected error in lip video generation", error=e)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

