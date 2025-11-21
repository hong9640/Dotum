"""
AI Service - Wav2Lip 립싱크 처리
"""

import os
import sys
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
        output_video_gs: str,
        target_fps: int = 18
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
                use_gpu=True,
                target_fps=target_fps
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
        """GPU 메모리에 따라 최적 배치 크기 자동 감지 (L4 GPU 최적화)"""
        if not torch.cuda.is_available():
            return 8
        
        gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        
        # L4 GPU (24GB) + STT 모델 고려: STT가 가볍다고 했으므로 Wav2Lip에 더 많은 메모리 할당 가능
        if gpu_memory_gb >= 40:
            return 48  # A100 등: 더 큰 배치
        elif gpu_memory_gb >= 24:  # L4 GPU (24GB)
            return 32  # L4: STT 모델 고려하여 32로 증가 (20 → 32)
        elif gpu_memory_gb >= 15:  # T4 GPU (15.75GB)
            return 16  # T4: 약간 증가 (12 → 16)
        elif gpu_memory_gb >= 12:
            return 12  # 12GB GPU
        else:
            return 8  # 8GB 이하
    
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
        use_gpu: bool = True,
        target_fps: int = 18
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
                
                # 원본 영상 해상도 추출 (FFprobe)
                original_resolution = await self._get_video_resolution(face_local)
                logger.info(f"Original video resolution: {original_resolution}")
                
                # 모델 경로
                model_local = os.path.join(settings.LOCAL_WAV2LIP_PATH, "checkpoints", "wav2lip_gan.pth")
                if not os.path.exists(model_local):
                    logger.error(f"Wav2Lip model not found: {model_local}")
                    return None
                
                # Wav2Lip 실행
                wav2lip_dir = settings.LOCAL_WAV2LIP_PATH
                inference_path = os.path.join(wav2lip_dir, "inference.py")
                output_temp = os.path.join(tmp_dir, "lipsynced_temp.mp4")  # 임시 출력
                output_local = os.path.join(tmp_dir, "lipsynced.mp4")  # 최종 출력
                
                # GPU 사용 여부 확인
                device = "cuda" if torch.cuda.is_available() and use_gpu else "cpu"
                logger.info(f"Running Wav2Lip on {device.upper()}")
                
                # GPU 파라미터 설정 (L4 GPU 최적화)
                if device == "cuda":
                    # L4 GPU (24GB): STT 모델과 공존 고려하여 최적 배치 크기 활용
                    # L4는 24GB이므로 Wav2Lip에 충분한 메모리 할당 가능
                    batch_size = str(self._optimal_batch_size)  # 자동 감지된 최적 크기 사용
                    face_det_batch = str(min(self._optimal_batch_size // 2, 24))  # 얼굴 감지 배치 증가 (최대 24)
                    logger.info(f"L4 GPU detected: Using batch_size={batch_size}, face_det_batch={face_det_batch}")
                else:
                    # CPU: 보수적 배치 크기
                    batch_size = "8"
                    face_det_batch = "4"
                
                # Python 실행 경로 확인 (venv 사용 시)
                python_exec = sys.executable if hasattr(sys, 'executable') else "python3"
                
                cmd = [
                    python_exec, inference_path,
                    "--checkpoint_path", model_local,
                    "--face", face_local,
                    "--audio", audio_local,
                    "--outfile", output_temp,  # 임시 파일로 출력
                    "--pads", "0", "15", "0", "0",  # 아래쪽 패딩 15픽셀 (턱 포함, 경계 최소화)
                    "--wav2lip_batch_size", batch_size,
                    "--face_det_batch_size", face_det_batch,
                    "--resize_factor", "1",  # 원본 해상도 유지 (품질 우선)
                    "--box", "-1", "-1", "-1", "-1",  # 자동 얼굴 감지
                    "--face_detector", "scrfd",  # SCRFD GPU detector 사용 (2-3배 빠름)
                ]
                
                logger.info(f"Running Wav2Lip inference: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=wav2lip_dir)
                
                if result.returncode != 0:
                    logger.error(f"Wav2Lip inference failed: {result.stderr}")
                    return None
                
                if not os.path.exists(output_temp):
                    logger.error(f"Wav2Lip output file not found: {output_temp}")
                    return None
                
                # 후처리: 원본 해상도로 리사이즈 (고품질 스케일링) + FPS 조정
                logger.info(f"Resizing output to original resolution: {original_resolution} @ {target_fps}fps with HIGH QUALITY (GPU accel: {torch.cuda.is_available()})")
                resize_success = await self._resize_video_to_resolution(
                    input_path=output_temp,
                    output_path=output_local,
                    resolution=original_resolution,
                    target_fps=target_fps,
                    original_video_path=face_local  # 원본 영상 경로 전달 (비트레이트 추출용)
                )
                
                if not resize_success or not os.path.exists(output_local):
                    logger.error("Failed to resize video to original resolution")
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
    
    async def _get_video_resolution(self, video_path: str) -> str:
        """
        FFprobe를 사용하여 영상의 해상도를 추출
        
        Returns:
            str: "widthxheight" 형식 (예: "1280x720")
        """
        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height",
                "-of", "csv=s=x:p=0",
                video_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            resolution = result.stdout.strip()
            logger.info(f"Detected video resolution: {resolution}")
            return resolution
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFprobe failed: {e.stderr}")
            return "1280x720"  # 기본값
        except Exception as e:
            logger.error(f"Failed to get video resolution: {e}")
            return "1280x720"  # 기본값
    
    async def _get_video_bitrate(self, video_path: str) -> str:
        """
        FFprobe를 사용하여 영상의 비트레이트를 추출
        
        Returns:
            str: 비트레이트 (예: "5000k") 또는 None
        """
        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=bit_rate",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            bitrate = result.stdout.strip()
            if bitrate and bitrate.isdigit():
                # bps를 kbps로 변환
                bitrate_kbps = int(int(bitrate) / 1000)
                logger.info(f"Detected video bitrate: {bitrate_kbps}k")
                return f"{bitrate_kbps}k"
            
            logger.warning("Could not detect bitrate, will use CRF mode")
            return None
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFprobe bitrate detection failed: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"Failed to get video bitrate: {e}")
            return None
    
    async def _resize_video_to_resolution(
        self,
        input_path: str,
        output_path: str,
        resolution: str,
        target_fps: int = 18,
        original_video_path: str = None
    ) -> bool:
        """
        FFmpeg를 사용하여 영상을 특정 해상도로 리사이즈 (하이브리드 방식)
        
        하이브리드 파이프라인:
        - CPU: 스케일링 (lanczos, 고품질) + FPS 조절
        - GPU: 인코딩 (h264_nvenc, 빠른 속도)
        - 오디오: 복사 (재인코딩 없음)
        
        Args:
            input_path: 입력 영상 경로
            output_path: 출력 영상 경로
            resolution: 목표 해상도 "widthxheight" (예: "1280x720")
            target_fps: 목표 프레임률 (기본값: 18fps)
            original_video_path: 원본 영상 경로 (비트레이트 추출용)
            
        Returns:
            bool: 성공 여부
        """
        try:
            # 원본 비트레이트 추출 (원본 화질 유지)
            original_bitrate = None
            if original_video_path:
                original_bitrate = await self._get_video_bitrate(original_video_path)
            
            # GPU 인코딩 가능 여부 확인
            gpu_encoding_available = torch.cuda.is_available()
            
            # 하이브리드 파이프라인: CPU 스케일링 + GPU 인코딩 (속도 최적화)
            # 스케일링 필터: fast_bilinear (lanczos보다 빠르지만 여전히 좋은 품질)
            cmd = [
                "ffmpeg",
                "-y",
                "-i", input_path,
                "-vf", f"scale={resolution}:flags=fast_bilinear,fps={target_fps}",  # 빠른 스케일링
                "-c:v", "h264_nvenc" if gpu_encoding_available else "libx264",  # GPU 인코딩 (가능 시)
                "-preset", "fast",  # 빠른 인코딩 (medium -> fast)
            ]
            
            # 비트레이트 또는 CRF 설정
            if original_bitrate:
                logger.info(f"Using original bitrate: {original_bitrate}")
                cmd.extend([
                    "-b:v", original_bitrate,
                    "-maxrate", original_bitrate,
                    "-bufsize", f"{int(original_bitrate.replace('k', '')) * 2}k",
                ])
            else:
                if gpu_encoding_available:
                    # NVENC: QP 21 (19보다 약간 빠르지만 여전히 고품질)
                    cmd.extend(["-rc", "constqp", "-qp", "21"])
                    logger.info("Using NVENC QP 21 (fast high quality)")
                else:
                    # CPU: CRF 18 (15보다 빠르지만 여전히 좋은 품질) + 멀티스레딩
                    cmd.extend(["-crf", "18", "-threads", "0"])
                    logger.info("Using CRF 18 with multithreading (fast high quality)")
            
            # 공통 옵션
            cmd.extend([
                "-pix_fmt", "yuv420p",
                "-c:a", "copy",  # 오디오 복사
                output_path
            ])
            
            logger.info(f"Hybrid pipeline (CPU scale + {'GPU' if gpu_encoding_available else 'CPU'} encode): {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info(f"Video resized successfully to {resolution} @ {target_fps}fps")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg resize failed: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Failed to resize video: {e}")
            return False


# AI 서비스 인스턴스
ai_service = AIService()

