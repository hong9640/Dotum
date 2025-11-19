"""
STT Service - Omnilingual ASR을 사용한 다국어 음성 인식
"""

import os
import time
import tempfile
from typing import Optional, List, Union, Dict
from api.utils.gcs_client import gcs_client
from api.core.logger import logger, log_step, log_success, log_error


class STTService:
    """
    Omnilingual ASR 기반 음성 인식 서비스
    
    지원:
    - 1600+ 언어 지원
    - 단일/배치 음성 인식
    - GCS 및 URL 기반 입력
    - 언어 자동 감지 또는 수동 지정
    """
    
    def __init__(self, model_size: str = "7B"):
        """
        STT 서비스 초기화
        
        Args:
            model_size: 모델 크기 (300M, 1B, 3B, 7B, 7B_ZS)
        """
        self.gcs_client = gcs_client
        self.model_size = model_size
        self.pipeline = None
        self._initialize_pipeline()
    
    def _initialize_pipeline(self):
        """Omnilingual ASR 파이프라인 초기화 (Lazy Loading)"""
        try:
            from omnilingual_asr.models.inference.pipeline import ASRInferencePipeline
            
            model_card = f"omniASR_LLM_{self.model_size}"
            log_step(f"Initializing Omnilingual ASR pipeline: {model_card}")
            
            self.pipeline = ASRInferencePipeline(model_card=model_card)
            
            log_success(f"Omnilingual ASR pipeline initialized: {model_card}")
            
        except ImportError as e:
            log_error(f"Failed to import omnilingual-asr: {e}")
            logger.error("Please install: pip install omnilingual-asr")
            self.pipeline = None
        except Exception as e:
            log_error(f"Failed to initialize Omnilingual ASR pipeline: {e}")
            self.pipeline = None
    
    async def transcribe_single(
        self,
        audio_source: str,
        lang: Optional[str] = None,
        is_gcs: bool = True
    ) -> Dict:
        """
        단일 오디오 파일 음성 인식
        
        Args:
            audio_source: GCS 경로 또는 URL
            lang: 언어 코드 (예: eng_Latn, kor_Hang). None이면 자동 감지
            is_gcs: True이면 GCS에서 다운로드, False이면 URL 직접 사용
            
        Returns:
            dict: {
                "success": bool,
                "transcription": str,
                "language": str or None,
                "process_time_ms": float
            }
        """
        start_time = time.time()
        temp_file = None
        
        try:
            if self.pipeline is None:
                raise ValueError("Omnilingual ASR pipeline not initialized")
            
            # 1. 오디오 파일 준비
            if is_gcs:
                log_step(f"Downloading audio from GCS: {audio_source}")
                temp_file = await self._download_audio_from_gcs(audio_source)
                if not temp_file:
                    raise ValueError("Failed to download audio from GCS")
                audio_path = temp_file
            else:
                audio_path = audio_source
            
            # 2. 음성 인식 실행
            log_step(f"Running transcription (lang: {lang or 'auto'})")
            transcriptions = self.pipeline.transcribe(
                [audio_path],
                lang=[lang] if lang else None,
                batch_size=1
            )
            
            if not transcriptions or len(transcriptions) == 0:
                raise ValueError("No transcription result")
            
            transcription = transcriptions[0]
            process_time_ms = (time.time() - start_time) * 1000
            
            log_success(
                f"Transcription completed ({process_time_ms:.0f}ms)",
                text=transcription[:100]
            )
            
            return {
                "success": True,
                "transcription": transcription,
                "language": lang,
                "process_time_ms": process_time_ms
            }
            
        except Exception as e:
            log_error(f"Transcription failed: {e}")
            return {
                "success": False,
                "transcription": "",
                "language": None,
                "process_time_ms": (time.time() - start_time) * 1000
            }
        
        finally:
            # 임시 파일 정리
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                    logger.debug(f"Cleaned up temp file: {temp_file}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temp file: {e}")
    
    async def transcribe_batch(
        self,
        audio_sources: List[Union[str, Dict]],
        langs: Optional[List[str]] = None,
        batch_size: int = 2,
        is_gcs: bool = True
    ) -> Dict:
        """
        배치 오디오 파일 음성 인식
        
        Args:
            audio_sources: GCS 경로 또는 URL 리스트
            langs: 각 오디오에 대한 언어 코드 리스트 (None이면 자동 감지)
            batch_size: 배치 처리 크기
            is_gcs: True이면 GCS에서 다운로드, False이면 URL 직접 사용
            
        Returns:
            dict: {
                "success": bool,
                "transcriptions": List[str],
                "languages": List[str] or None,
                "process_time_ms": float
            }
        """
        start_time = time.time()
        temp_files = []
        
        try:
            if self.pipeline is None:
                raise ValueError("Omnilingual ASR pipeline not initialized")
            
            # 1. 오디오 파일 준비
            audio_paths = []
            for audio_source in audio_sources:
                if is_gcs:
                    log_step(f"Downloading audio from GCS: {audio_source}")
                    temp_file = await self._download_audio_from_gcs(audio_source)
                    if not temp_file:
                        raise ValueError(f"Failed to download audio: {audio_source}")
                    temp_files.append(temp_file)
                    audio_paths.append(temp_file)
                else:
                    audio_paths.append(audio_source)
            
            # 2. 배치 음성 인식 실행
            log_step(f"Running batch transcription ({len(audio_paths)} files, batch_size={batch_size})")
            transcriptions = self.pipeline.transcribe(
                audio_paths,
                lang=langs if langs else None,
                batch_size=batch_size
            )
            
            if not transcriptions:
                raise ValueError("No transcription results")
            
            process_time_ms = (time.time() - start_time) * 1000
            
            log_success(
                f"Batch transcription completed ({process_time_ms:.0f}ms)",
                count=len(transcriptions)
            )
            
            return {
                "success": True,
                "transcriptions": transcriptions,
                "languages": langs,
                "process_time_ms": process_time_ms
            }
            
        except Exception as e:
            log_error(f"Batch transcription failed: {e}")
            return {
                "success": False,
                "transcriptions": [],
                "languages": None,
                "process_time_ms": (time.time() - start_time) * 1000
            }
        
        finally:
            # 임시 파일 정리
            cleaned_count = 0
            for temp_file in temp_files:
                if temp_file and os.path.exists(temp_file):
                    try:
                        os.unlink(temp_file)
                        cleaned_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to clean up {temp_file}: {e}")
            if cleaned_count > 0:
                logger.debug(f"Cleaned up {cleaned_count} temporary files")
    
    async def _download_audio_from_gcs(self, gs_path: str) -> Optional[str]:
        """
        GCS에서 오디오 파일 다운로드
        
        Args:
            gs_path: GCS 경로 (gs://bucket/path/to/audio.wav)
            
        Returns:
            str: 로컬 임시 파일 경로 또는 None
        """
        try:
            # 임시 파일 생성 (확장자 유지)
            ext = os.path.splitext(gs_path)[1] or ".wav"
            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=ext,
                prefix="stt_audio_"
            )
            temp_path = temp_file.name
            temp_file.close()
            
            # GCS에서 다운로드
            if not self.gcs_client.download_file(gs_path, temp_path):
                logger.error(f"Failed to download audio from GCS: {gs_path}")
                return None
            
            logger.debug(f"Audio downloaded to: {temp_path}")
            return temp_path
            
        except Exception as e:
            logger.error(f"Failed to download audio from GCS: {e}")
            return None
    
    def get_supported_languages(self) -> List[str]:
        """
        지원되는 언어 목록 조회
        
        Returns:
            List[str]: 언어 코드 리스트 (예: ["eng_Latn", "kor_Hang", ...])
        """
        try:
            from omnilingual_asr.models.wav2vec2_llama.lang_ids import supported_langs
            return list(supported_langs)
        except ImportError:
            logger.error("Failed to import supported_langs from omnilingual-asr")
            return []
    
    def is_language_supported(self, lang: str) -> bool:
        """
        특정 언어 지원 여부 확인
        
        Args:
            lang: 언어 코드 (예: eng_Latn, kor_Hang)
            
        Returns:
            bool: 지원 여부
        """
        supported = self.get_supported_languages()
        return lang in supported


# STT 서비스 인스턴스 (Lazy Loading)
_stt_service: Optional[STTService] = None


def get_stt_service(model_size: str = "7B") -> STTService:
    """
    STT 서비스 싱글톤 인스턴스 조회
    
    Args:
        model_size: 모델 크기 (300M, 1B, 3B, 7B)
        
    Returns:
        STTService: STT 서비스 인스턴스
    """
    global _stt_service
    
    if _stt_service is None or _stt_service.model_size != model_size:
        _stt_service = STTService(model_size=model_size)
    
    return _stt_service

