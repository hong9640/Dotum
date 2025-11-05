"""
최적화된 AI Service
- FreeVC 모델 사전 로드
- subprocess 제거
- 직접 추론 실행
"""

import os
import subprocess
import tempfile
import time
import torch
import asyncio
from typing import Optional
from api.utils.gcs_client import gcs_client
from api.core.config import settings
from api.core.logger import logger, log_step, log_success, log_error
from api.service.freevc_optimized import load_freevc_models, infer_freevc


class AIServiceOptimized:
    """최적화된 AI 모델 서비스 클래스"""
    
    def __init__(self):
        self.gcs_client = gcs_client
        self._optimal_batch_size = self._detect_optimal_batch_size()
        self._models_loaded = False
    
    def ensure_models_loaded(self):
        """모델이 로드되었는지 확인하고 필요시 로드"""
        if not self._models_loaded:
            logger.info("Loading models for the first time...")
            load_freevc_models()
            self._models_loaded = True
    
    async def process_lip_video_pipeline(
        self,
        user_video_gs: str,
        word: str,
        output_video_gs: str,
        tts_lang: str = "ko"
    ) -> dict:
        """
        전체 립싱크 영상 생성 파이프라인 실행 (최적화 버전)
        
        Args:
            user_video_gs: 사용자 업로드 영상 GCS 경로
            word: 사용자 발화 단어
            output_video_gs: 결과 영상 업로드 경로
            tts_lang: TTS 언어 코드
            
        Returns:
            dict: 처리 결과 정보
        """
        start_time = time.time()
        temp_files = []
        step_times = {}
        
        try:
            # 모델 사전 로드 확인
            self.ensure_models_loaded()
            
            # 1. GCS에서 영상 다운로드
            step_start = time.time()
            log_step("Downloading video from GCS to tmp")
            video_local_path = await self._download_video_to_tmp(user_video_gs)
            if not video_local_path:
                raise ValueError("Failed to download video from GCS")
            temp_files.append(video_local_path)
            step_times["1_download_video"] = time.time() - step_start
            log_success(f"Video downloaded ({step_times['1_download_video']:.2f}s)", path=video_local_path)
            
            # 2. 병렬처리: 오디오 추출 + TTS 생성
            step_start = time.time()
            log_step("Parallel processing: extracting audio + generating TTS")
            results = await asyncio.gather(
                self._extract_audio_from_video(video_local_path),
                self._generate_tts_audio(word, tts_lang),
                return_exceptions=True
            )
            
            extracted_audio_path, tts_audio_path = results
            
            if isinstance(extracted_audio_path, Exception) or not extracted_audio_path:
                raise ValueError("Failed to extract audio from video")
            temp_files.append(extracted_audio_path)
            
            if isinstance(tts_audio_path, Exception) or not tts_audio_path:
                raise ValueError("Failed to generate TTS audio")
            temp_files.append(tts_audio_path)
            step_times["2_audio_tts"] = time.time() - step_start
            log_success(f"Audio + TTS completed ({step_times['2_audio_tts']:.2f}s)")
            
            # 3. FreeVC 음성 변환 (최적화 버전!)
            step_start = time.time()
            log_step("Running FreeVC inference (OPTIMIZED)")
            freevc_output_path = await self._run_freevc_inference_optimized(
                src_audio_path=extracted_audio_path,
                ref_audio_path=tts_audio_path,
                output_prefix=f"user_{int(time.time())}"
            )
            if not freevc_output_path:
                raise ValueError("Failed to run FreeVC inference")
            temp_files.append(freevc_output_path)
            step_times["3_freevc"] = time.time() - step_start
            log_success(f"FreeVC completed ({step_times['3_freevc']:.2f}s) [OPTIMIZED]", path=freevc_output_path)
            
            # 4. Wav2Lip 립싱크
            step_start = time.time()
            log_step("Running Wav2Lip inference and uploading to GCS")
            result_video_path = await self._run_wav2lip_inference(
                face_video_path=video_local_path,
                audio_path=freevc_output_path,
                output_gs_path=output_video_gs,
                use_gpu=True
            )
            if not result_video_path:
                raise ValueError("Failed to run Wav2Lip inference or upload to GCS")
            step_times["4_wav2lip"] = time.time() - step_start
            log_success(f"Wav2Lip completed ({step_times['4_wav2lip']:.2f}s)", path=result_video_path)
            
            process_time_ms = (time.time() - start_time) * 1000
            
            # 성능 분석 로그
            logger.info("=" * 60)
            logger.info("Performance Analysis [OPTIMIZED]:")
            logger.info(f"  1. Download Video:    {step_times['1_download_video']:>7.2f}s ({step_times['1_download_video']/process_time_ms*100000:.1f}%)")
            logger.info(f"  2. Audio + TTS:       {step_times['2_audio_tts']:>7.2f}s ({step_times['2_audio_tts']/process_time_ms*100000:.1f}%)")
            logger.info(f"  3. FreeVC (opt):      {step_times['3_freevc']:>7.2f}s ({step_times['3_freevc']/process_time_ms*100000:.1f}%)")
            logger.info(f"  4. Wav2Lip:           {step_times['4_wav2lip']:>7.2f}s ({step_times['4_wav2lip']/process_time_ms*100000:.1f}%)")
            logger.info(f"  Total:                {process_time_ms/1000:>7.2f}s (100.0%)")
            logger.info("=" * 60)
            
            return {
                "success": True,
                "result_video_gs": output_video_gs,
                "process_time_ms": process_time_ms
            }
            
        except Exception as e:
            log_error(f"Pipeline failed: {e}")
            raise
        
        finally:
            # 임시 파일 정리 (로그 간소화)
            cleaned_count = 0
            for temp_file in temp_files:
                if temp_file and os.path.exists(temp_file):
                    try:
                        os.unlink(temp_file)
                        cleaned_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to clean up {temp_file}: {e}")
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} temporary files")
    
    async def _run_freevc_inference_optimized(
        self,
        src_audio_path: str,
        ref_audio_path: str,
        output_prefix: str
    ) -> Optional[str]:
        """
        최적화된 FreeVC 추론 (subprocess 없이)
        
        Args:
            src_audio_path: 원본 오디오 경로
            ref_audio_path: 참조 오디오 경로
            output_prefix: 출력 파일명 접두사
            
        Returns:
            Optional[str]: 생성된 오디오 경로
        """
        try:
            # 출력 파일 경로
            output_path = f"/tmp/{output_prefix}_freevc_out.wav"
            
            # 비동기 실행을 위해 별도 스레드에서 실행
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(
                None,
                infer_freevc,
                src_audio_path,
                ref_audio_path,
                output_path
            )
            
            if success and os.path.exists(output_path):
                return output_path
            else:
                logger.error("FreeVC inference failed")
                return None
                
        except Exception as e:
            logger.error(f"Failed to run optimized FreeVC inference: {e}")
            return None
    
    def _detect_optimal_batch_size(self) -> int:
        """GPU 메모리에 따라 최적 배치 크기 자동 감지"""
        if not torch.cuda.is_available():
            return 8
        
        gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        
        if gpu_memory_gb >= 40:
            return 64
        elif gpu_memory_gb >= 24:
            return 32
        elif gpu_memory_gb >= 16:
            return 24
        else:
            return 16
    
    async def _generate_tts_audio(self, text: str, lang: str = "ko") -> Optional[str]:
        """TTS로 오디오 생성"""
        try:
            import hashlib
            text_hash = hashlib.md5(text.encode()).hexdigest()
            tts_filename = f"{text_hash}_{lang}.wav"
            tts_local_path = f"/tmp/{tts_filename}"
            
            if os.path.exists(tts_local_path):
                logger.info(f"TTS file already exists locally: {tts_local_path}")
                return tts_local_path
            
            from gtts import gTTS
            tts = gTTS(text=text, lang=lang, slow=False)
            tts.save(tts_local_path)
            
            logger.info(f"TTS generated successfully: {tts_local_path}")
            return tts_local_path
                
        except Exception as e:
            logger.error(f"Failed to generate TTS: {e}")
            return None
    
    async def _download_video_to_tmp(self, video_gs_path: str) -> Optional[str]:
        """GCS에서 영상 다운로드"""
        try:
            video_filename = f"video_{int(time.time())}.mp4"
            video_local_path = f"/tmp/{video_filename}"
            
            if not self.gcs_client.download_file(video_gs_path, video_local_path):
                logger.error(f"Failed to download video: {video_gs_path}")
                return None
            
            logger.info(f"Video downloaded to tmp: {video_local_path}")
            return video_local_path
            
        except Exception as e:
            logger.error(f"Failed to download video to tmp: {e}")
            return None
    
    async def _extract_audio_from_video(self, video_local_path: str) -> Optional[str]:
        """영상에서 오디오 추출"""
        try:
            audio_filename = f"extracted_audio_{int(time.time())}.wav"
            audio_local_path = f"/tmp/{audio_filename}"
            
            cmd = [
                "ffmpeg", "-y",
                "-threads", "8",
                "-i", video_local_path,
                "-vn",
                "-acodec", "pcm_s16le",
                "-ar", "16000",
                "-ac", "1",
                audio_local_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"Failed to extract audio: {result.stderr}")
                return None
            
            logger.info(f"Audio extracted from video: {audio_local_path}")
            return audio_local_path
                
        except Exception as e:
            logger.error(f"Failed to extract audio from video: {e}")
            return None
    
    async def _run_wav2lip_inference(
        self,
        face_video_path: str,
        audio_path: str,
        output_gs_path: str,
        use_gpu: bool = True
    ) -> Optional[str]:
        """Wav2Lip 립싱크 (GPU 최적화 + Static Face Detection)"""
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                # 오디오 파일 처리
                audio_local = os.path.join(tmp_dir, "audio.wav")
                import shutil
                shutil.copy2(audio_path, audio_local)
                
                # 영상 파일 처리
                face_local = os.path.join(tmp_dir, "face_input.mp4")
                shutil.copy2(face_video_path, face_local)
                
                # 모델 경로
                model_local = os.path.join(settings.LOCAL_WAV2LIP_PATH, "checkpoints", "Wav2Lip_gan.pth")
                if not os.path.exists(model_local):
                    logger.error(f"Wav2Lip model not found: {model_local}")
                    return None
                
                # Wav2Lip 실행
                wav2lip_dir = settings.LOCAL_WAV2LIP_PATH
                inference_path = os.path.join(wav2lip_dir, "inference.py")
                output_local = os.path.join(tmp_dir, "lipsynced.mp4")
                
                # GPU 사용 여부 확인
                device = "cuda" if torch.cuda.is_available() and use_gpu else "cpu"
                logger.info(f"Running Wav2Lip on {device.upper()}")
                
                # GPU 최적화 파라미터 설정
                if device == "cuda":
                    # GPU: 더 큰 배치 크기 및 Static Face Detection
                    batch_size = str(self._optimal_batch_size)
                    face_det_batch = str(min(self._optimal_batch_size // 2, 16))
                else:
                    # CPU: 보수적 배치 크기
                    batch_size = "8"
                    face_det_batch = "4"
                
                cmd = [
                    "python3", inference_path,
                    "--checkpoint_path", model_local,
                    "--face", face_local,
                    "--audio", audio_local,
                    "--outfile", output_local,
                    "--pads", "0", "20", "0", "0",
                    "--wav2lip_batch_size", batch_size,
                    "--face_det_batch_size", face_det_batch,
                    "--resize_factor", "2",  # GPU에서는 품질 향상 (960x540)
                    "--nosmooth",  # Face detection smoothing 비활성화 (속도 향상)
                    "--box", "-1", "-1", "-1", "-1",  # Static Face Detection (최대 성능 향상!)
                ]
                
                logger.info(f"Running Wav2Lip inference: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=wav2lip_dir)
                
                if result.returncode != 0:
                    logger.error(f"Wav2Lip inference failed: {result.stderr}")
                    return None
                
                if not os.path.exists(output_local):
                    logger.error(f"Wav2Lip output file not found: {output_local}")
                    return None
                
                # GCS에 업로드
                logger.info(f"Uploading to GCS: {output_local} -> {output_gs_path}")
                if not self.gcs_client.upload_file(output_local, output_gs_path):
                    logger.error("Failed to upload Wav2Lip output to GCS")
                    return None
                    
                logger.info(f"Wav2Lip inference completed: {output_gs_path}")
                return output_gs_path
                    
        except Exception as e:
            logger.error(f"Failed to run Wav2Lip inference: {e}")
            return None


# 최적화된 AI 서비스 인스턴스
ai_service_optimized = AIServiceOptimized()

