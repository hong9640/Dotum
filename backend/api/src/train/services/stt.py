"""
STT Service
ML 서버에 STT 요청을 보내고 결과를 처리하는 서비스
"""
import httpx
import logging
from typing import Optional, Dict, Any

from api.core.config import settings

logger = logging.getLogger(__name__)


class SttService:
    """STT 처리 서비스"""
    
    @staticmethod
    async def transcribe_audio(
        audio_gs_path: str,
        timeout: float = 120.0
    ) -> Optional[Dict[str, Any]]:
        """
        ML 서버에 STT 요청을 보내고 결과를 반환
        
        Args:
            audio_gs_path: GCS 오디오 파일 경로 (예: "gs://bucket/path/to/audio.wav")
            timeout: 요청 타임아웃 (초)
            
        Returns:
            STT 결과 딕셔너리:
            {
                "success": bool,
                "transcription": str,
                "language": str,
                "process_time_ms": float
            }
            실패 시 None 반환
        """
        STT_API_URL = f"{settings.ML_SERVER_URL}/api/v1/stt/transcribe"
        
        payload = {
            "audio_gs": audio_gs_path
        }
        
        try:
            logger.info(f"[STT] ML 서버로 STT 요청 전송 중... URL: {STT_API_URL}")
            logger.info(f"[STT] Payload: {payload}")
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(STT_API_URL, json=payload)
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"[STT] ✅ STT 요청 성공: {result}")
                
                # 응답 검증
                if not result.get("success"):
                    logger.error(f"[STT] ❌ STT 처리 실패: {result}")
                    return None
                
                return result
                
        except httpx.TimeoutException as e:
            logger.error(f"[STT] ❌ STT 요청 타임아웃: {e}")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"[STT] ❌ STT 요청 HTTP 오류: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"[STT] ❌ STT 요청 중 예외 발생: {e}", exc_info=True)
            return None


async def request_stt_transcription(
    audio_gs_path: str,
    timeout: float = 120.0
) -> Optional[Dict[str, Any]]:
    """
    STT 요청을 보내는 헬퍼 함수
    
    Args:
        audio_gs_path: GCS 오디오 파일 경로
        timeout: 요청 타임아웃 (초)
        
    Returns:
        STT 결과 또는 None
    """
    return await SttService.transcribe_audio(audio_gs_path, timeout)

