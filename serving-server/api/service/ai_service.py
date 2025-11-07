"""
AI Service - Wav2Lip 립싱크 처리
"""

import os
import subprocess
import tempfile
import time
import torch
import shutil
from typing import Optional
from api.utils.gcs_client import gcs_client
from api.core.config import settings
from api.core.logger import logger, log_step, log_success, log_error


class AIService:
    """AI 모델 서비스 클래스"""
    
    def __init__(self):
        self.gcs_client = gcs_client
        self._optimal_batch_size = self._detect_optimal_batch_size()
    
    async def process_lip_video_pipeline(
        self,
        user_video_gs: str,
        gen_audio_gs: str,
        output_video_gs: str
    ) -> dict:
        """
        립싱크 영상 생성 파이프라인 실행
        
        Args:
            user_video_gs: 사용자 업로드 영상 GCS 경로
            gen_audio_gs: 생성된 오디오 GCS 경로
            output_video_gs: 결과 영상 업로드 경로
            
        Returns:
            dict: 처리 결과 정보
        """
        start_time = time.time()
        temp_files = []
        step_times = {}
        
        try:
            # 1. GCS에서 영상 다운로드
            step_start = time.time()
            log_step("Downloading video from GCS")
            video_local_path = await self._download_file_from_gcs(
                user_video_gs, 
                f"video_{int(time.time())}.mp4"
            )
            if not video_local_path:
                raise ValueError("Failed to download video from GCS")
            temp_files.append(video_local_path)
            step_times["1_download_video"] = time.time() - step_start
            log_success(f"Video downloaded ({step_times['1_download_video']:.2f}s)", path=video_local_path)
            
            # 2. GCS에서 오디오 다운로드
            step_start = time.time()
            log_step("Downloading audio from GCS")
            audio_local_path = await self._download_file_from_gcs(
                gen_audio_gs, 
                f"audio_{int(time.time())}.wav"
            )
            if not audio_local_path:
                raise ValueError("Failed to download audio from GCS")
            temp_files.append(audio_local_path)
            step_times["2_download_audio"] = time.time() - step_start
            log_success(f"Audio downloaded ({step_times['2_download_audio']:.2f}s)", path=audio_local_path)
            
            # 3. Wav2Lip 립싱크
            step_start = time.time()
            log_step("Running Wav2Lip inference and uploading to GCS")
            result_video_path = await self._run_wav2lip_inference(
                face_video_path=video_local_path,
                audio_path=audio_local_path,
                output_gs_path=output_video_gs,
                use_gpu=True
            )
            if not result_video_path:
                raise ValueError("Failed to run Wav2Lip inference or upload to GCS")
            step_times["3_wav2lip"] = time.time() - step_start
            log_success(f"Wav2Lip completed ({step_times['3_wav2lip']:.2f}s)", path=result_video_path)
            
            process_time_ms = (time.time() - start_time) * 1000
            
            # 성능 분석 로그
            logger.info("=" * 60)
            logger.info("Performance Analysis:")
            logger.info(f"  1. Download Video:    {step_times['1_download_video']:>7.2f}s ({step_times['1_download_video']/process_time_ms*100000:.1f}%)")
            logger.info(f"  2. Download Audio:    {step_times['2_download_audio']:>7.2f}s ({step_times['2_download_audio']/process_time_ms*100000:.1f}%)")
            logger.info(f"  3. Wav2Lip:           {step_times['3_wav2lip']:>7.2f}s ({step_times['3_wav2lip']/process_time_ms*100000:.1f}%)")
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
                logger.info(f"Cleaned up {cleaned_count} temporary files")
    
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
    
    async def _download_file_from_gcs(self, gs_path: str, filename: str) -> Optional[str]:
        """GCS에서 파일 다운로드"""
        try:
            local_path = f"/tmp/{filename}"
            
            if not self.gcs_client.download_file(gs_path, local_path):
                logger.error(f"Failed to download file: {gs_path}")
                return None
            
            logger.info(f"File downloaded to tmp: {local_path}")
            return local_path
            
        except Exception as e:
            logger.error(f"Failed to download file from GCS: {e}")
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
                shutil.copy2(audio_path, audio_local)
                
                # 영상 파일 처리
                face_local = os.path.join(tmp_dir, "face_input.mp4")
                shutil.copy2(face_video_path, face_local)
                
                # 모델 경로
                model_local = os.path.join(settings.LOCAL_WAV2LIP_PATH, "checkpoints", "Wav2Lip_v1.pth")
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


# AI 서비스 인스턴스
ai_service = AIService()

