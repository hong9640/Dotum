import os
import subprocess
import tempfile
import time
import torch
import asyncio
from typing import Optional, Tuple
from api.utils.gcs_client import gcs_client
from api.core.config import settings
from api.core.logger import logger, log_step, log_success, log_error


# ✅ Added: 전역 모델 캐시 (FreeVC / Wav2Lip)
_freevc_cache = {
    "net_g": None,
    "cmodel": None,
    "smodel": None,
}

_wav2lip_cache = {
    "model_loaded": False
}


class AIService:
    """AI 모델 서비스 클래스"""
    
    def __init__(self):
        self.gcs_client = gcs_client
        self._optimal_batch_size = self._detect_optimal_batch_size()
    
    async def process_lip_video_pipeline(
        self,
        user_video_gs: str,
        word: str,
        output_video_gs: str,
        tts_lang: str = "ko"
    ) -> dict:
        """
        전체 립싱크 영상 생성 파이프라인 실행
        
        Args:
            user_video_gs: 사용자 업로드 영상 GCS 경로
            word: 사용자 발화 단어
            output_video_gs: 결과 영상 업로드 경로
            tts_lang: TTS 언어 코드
            
        Returns:
            dict: 처리 결과 정보 {
                "success": bool,
                "result_video_gs": str,
                "process_time_ms": float
            }
        """
        import time
        start_time = time.time()
        temp_files = []
        
        # 타이밍 측정용
        step_times = {}
        
        try:
            # 1. GCS에서 영상을 tmp/ 경로로 다운로드
            step_start = time.time()
            log_step("Downloading video from GCS to tmp")
            video_local_path = await self.download_video_to_tmp(user_video_gs)
            if not video_local_path:
                raise ValueError("Failed to download video from GCS")
            temp_files.append(video_local_path)
            step_times["1_download_video"] = time.time() - step_start
            log_success(f"Video downloaded to tmp ({step_times['1_download_video']:.2f}s)", path=video_local_path)
            
            # 2. 병렬처리: 영상 오디오화 + TTS 생성
            step_start = time.time()
            log_step("Parallel processing: extracting audio + generating TTS")
            results = await asyncio.gather(
                self.extract_audio_from_video(video_local_path),
                self.generate_tts_audio(word, tts_lang),
                return_exceptions=True
            )
            
            extracted_audio_path, tts_audio_path = results
            
            # 오디오 추출 결과 확인
            if isinstance(extracted_audio_path, Exception) or not extracted_audio_path:
                raise ValueError("Failed to extract audio from video")
            temp_files.append(extracted_audio_path)
            
            # TTS 생성 결과 확인
            if isinstance(tts_audio_path, Exception) or not tts_audio_path:
                raise ValueError("Failed to generate TTS audio")
            temp_files.append(tts_audio_path)
            step_times["2_audio_tts"] = time.time() - step_start
            log_success(f"Audio extraction + TTS completed ({step_times['2_audio_tts']:.2f}s)", 
                       audio=extracted_audio_path, tts=tts_audio_path)
            
            # 3. FreeVC 음성 변환
            step_start = time.time()
            log_step("Running FreeVC inference")
            freevc_output_path = await self.run_freevc_inference(
                src_audio_path=extracted_audio_path,
                ref_audio_path=tts_audio_path,
                output_prefix=f"user_{int(time.time())}"
            )
            if not freevc_output_path:
                raise ValueError("Failed to run FreeVC inference")
            temp_files.append(freevc_output_path)
            step_times["3_freevc"] = time.time() - step_start
            log_success(f"FreeVC inference completed ({step_times['3_freevc']:.2f}s)", path=freevc_output_path)
            
            # 4. Wav2Lip 립싱크 및 GCS 업로드 (로컬 영상 파일 사용)
            step_start = time.time()
            log_step("Running Wav2Lip inference and uploading to GCS")
            result_video_path = await self.run_wav2lip_inference(
                face_video_path=video_local_path,
                audio_path=freevc_output_path,
                output_gs_path=output_video_gs,
                use_gpu=True
            )
            if not result_video_path:
                raise ValueError("Failed to run Wav2Lip inference or upload to GCS")
            step_times["4_wav2lip"] = time.time() - step_start
            log_success(f"Wav2Lip inference completed and uploaded ({step_times['4_wav2lip']:.2f}s)", path=result_video_path)
            
            process_time_ms = (time.time() - start_time) * 1000
            
            # 성능 분석 로그
            logger.info("=" * 60)
            logger.info("Performance Analysis:")
            logger.info(f"  1. Download Video:    {step_times['1_download_video']:>7.2f}s ({step_times['1_download_video']/process_time_ms*100000:.1f}%)")
            logger.info(f"  2. Audio + TTS:       {step_times['2_audio_tts']:>7.2f}s ({step_times['2_audio_tts']/process_time_ms*100000:.1f}%)")
            logger.info(f"  3. FreeVC:            {step_times['3_freevc']:>7.2f}s ({step_times['3_freevc']/process_time_ms*100000:.1f}%)")
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
    
    def _detect_optimal_batch_size(self) -> int:
        """GPU 메모리에 따라 최적 배치 크기 자동 감지"""
        if not torch.cuda.is_available():
            return 8
        
        gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        
        if gpu_memory_gb >= 40:  # A100
            logger.info(f"Detected A100 ({gpu_memory_gb:.1f}GB) - using batch_size=64")
            return 64
        elif gpu_memory_gb >= 24:  # RTX 3090, A5000
            logger.info(f"High-end GPU ({gpu_memory_gb:.1f}GB) - using batch_size=32")
            return 32
        elif gpu_memory_gb >= 16:
            return 24
        else:
            return 16
    
    async def generate_tts_audio(self, text: str, lang: str = "ko") -> Optional[str]:
        """
        TTS로 오디오 생성 (gTTS 사용)
        
        Args:
            text: 변환할 텍스트
            lang: 언어 코드
            
        Returns:
            Optional[str]: 생성된 TTS 오디오의 로컬 경로
        """
        try:
            # TTS 파일명 생성 (텍스트 해시 기반)
            import hashlib
            text_hash = hashlib.md5(text.encode()).hexdigest()
            tts_filename = f"{text_hash}_{lang}.wav"
            tts_local_path = f"/tmp/{tts_filename}"
            
            # 이미 로컬에 TTS 파일이 존재하는지 확인
            if os.path.exists(tts_local_path):
                logger.info(f"TTS file already exists locally: {tts_local_path}")
                return tts_local_path
            
            # gTTS 사용
            from gtts import gTTS
            
            # gTTS 객체 생성
            tts = gTTS(text=text, lang=lang, slow=False)
            
            # 로컬 tmp 파일에 저장
            tts.save(tts_local_path)
            
            logger.info(f"TTS generated successfully: {tts_local_path}")
            return tts_local_path
                
        except Exception as e:
            logger.error(f"Failed to generate TTS: {e}")
            return None

    async def download_video_to_tmp(self, video_gs_path: str) -> Optional[str]:
        """
        GCS에서 영상을 tmp/ 경로로 다운로드
        
        Args:
            video_gs_path: GCS 영상 경로
            
        Returns:
            Optional[str]: 다운로드된 영상의 로컬 경로
        """
        try:
            # tmp 디렉토리에 저장
            video_filename = f"video_{int(time.time())}.mp4"
            video_local_path = f"/tmp/{video_filename}"
            
            # GCS에서 영상 다운로드
            if not self.gcs_client.download_file(video_gs_path, video_local_path):
                logger.error(f"Failed to download video: {video_gs_path}")
                return None
            
            logger.info(f"Video downloaded to tmp: {video_local_path}")
            return video_local_path
            
        except Exception as e:
            logger.error(f"Failed to download video to tmp: {e}")
            return None
    
    async def extract_audio_from_video(self, video_local_path: str) -> Optional[str]:
        """
        로컬 영상에서 오디오 추출
        
        Args:
            video_local_path: 로컬 영상 경로
            
        Returns:
            Optional[str]: 추출된 오디오의 로컬 경로
        """
        try:
            # 오디오 추출
            audio_filename = f"extracted_audio_{int(time.time())}.wav"
            audio_local_path = f"/tmp/{audio_filename}"
            
            cmd = [
                "ffmpeg", "-y",
                "-threads", "8",     # 병렬 처리
                "-i", video_local_path,
                "-vn",  # 비디오 스트림 제거
                "-acodec", "pcm_s16le",  # 오디오 코덱
                "-ar", "16000",  # 샘플레이트
                "-ac", "1",  # 모노
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
    
    async def run_freevc_inference(
        self, 
        src_audio_path: str, 
        ref_audio_path: str,
        output_prefix: str
    ) -> Optional[str]:
        """
        FreeVC 모델로 음성 변환 실행
        
        Args:
            src_audio_path: 원본 오디오 파일 경로 (로컬 또는 GCS)
            ref_audio_path: 참조 오디오 파일 경로 (로컬 또는 GCS)
            output_prefix: 출력 파일명 접두사
            
        Returns:
            Optional[str]: 생성된 오디오의 로컬 경로
        """
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                # GCS에서 파일 다운로드 (GCS 경로인 경우만)
                src_local = os.path.join(tmp_dir, "src_audio.wav")
                ref_local = os.path.join(tmp_dir, "ref_audio.wav")
                
                # src_audio_path가 로컬 경로인지 확인
                if src_audio_path.startswith("gs://"):
                    if not self.gcs_client.download_file(src_audio_path, src_local):
                        logger.error(f"Failed to download src audio: {src_audio_path}")
                        return None
                else:
                    # 로컬 경로인 경우 복사
                    import shutil
                    shutil.copy2(src_audio_path, src_local)
                    logger.info(f"Using local audio file: {src_audio_path}")
                
                # ref_audio_path가 로컬 경로인지 확인
                if ref_audio_path.startswith("gs://"):
                    if not self.gcs_client.download_file(ref_audio_path, ref_local):
                        logger.error(f"Failed to download ref audio: {ref_audio_path}")
                        return None
                else:
                    # 로컬 경로인 경우 복사
                    import shutil
                    shutil.copy2(ref_audio_path, ref_local)
                    logger.info(f"Using local ref audio file: {ref_audio_path}")
                
                # 로컬 모델 파일 경로 설정
                model_local = os.path.join(settings.LOCAL_FREEVC_PATH, "checkpoints", "freevc-s.pth")
                config_local = os.path.join(settings.LOCAL_FREEVC_PATH, "configs", "freevc-s.json")
                
                # 로컬 모델 파일 존재 확인
                if not os.path.exists(model_local):
                    logger.error(f"FreeVC model not found locally: {model_local}")
                    return None
                
                if not os.path.exists(config_local):
                    logger.error(f"FreeVC config not found locally: {config_local}")
                    return None
                
                # 출력 파일 경로 설정
                output_local = os.path.join(tmp_dir, "freevc_out.wav")
                
                # 로컬 FreeVC 디렉토리 사용
                freevc_dir = settings.LOCAL_FREEVC_PATH
                
                # 로컬 FreeVC 파일들 존재 확인
                freevc_infer_path = os.path.join(freevc_dir, "freevc_infer.py")
                if not os.path.exists(freevc_infer_path):
                    logger.error(f"FreeVC inference script not found locally: {freevc_infer_path}")
                    return None
                
                convert_path = os.path.join(freevc_dir, "convert.py")
                if not os.path.exists(convert_path):
                    logger.error(f"FreeVC CPU convert script not found locally: {convert_path}")
                    return None
                
                # 필수 파일들 존재 확인 (CPU 모드 우선)
                essential_files = [
                    "commons.py", "data_utils.py", "downsample.py",
                    "losses.py", "mel_processing.py", "models.py", "modules.py",
                    "utils_cpu.py", "preprocess_flist.py", "preprocess_spk.py",
                    "preprocess_sr_cpu.py", "preprocess_ssl_cpu.py", "train.py"
                ]
                
                for filename in essential_files:
                    file_path = os.path.join(freevc_dir, filename)
                    if not os.path.exists(file_path):
                        logger.error(f"FreeVC essential file not found locally: {file_path}")
                        return None
                
                # 하위 디렉토리들 존재 확인
                required_dirs = [
                    "hifigan", "speaker_encoder", "speaker_encoder/data_objects", "wavlm"
                ]
                
                for dir_name in required_dirs:
                    dir_path = os.path.join(freevc_dir, dir_name)
                    if not os.path.exists(dir_path):
                        logger.error(f"FreeVC directory not found locally: {dir_path}")
                        return None
                
                # FreeVC 추론 실행
                cmd = [
                    "python3", freevc_infer_path,
                    "--hpfile", config_local,
                    "--ptfile", model_local,
                    "--src_audio", src_local,
                    "--ref_audio", ref_local,
                    "--out", output_local,
                    "--outdir", tmp_dir,
                    "--use_timestamp",
                    "--python_bin", "python3"
                ]
                
                logger.info(f"Running FreeVC inference: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=freevc_dir)
                
                if result.returncode != 0:
                    logger.error(f"FreeVC inference failed: {result.stderr}")
                    return None
                
                # 결과 파일을 로컬 tmp에 저장
                output_tmp_path = f"/tmp/{output_prefix}_freevc_out.wav"
                import shutil
                shutil.copy2(output_local, output_tmp_path)
                
                logger.info(f"FreeVC inference completed: {output_tmp_path}")
                return output_tmp_path
                    
        except Exception as e:
            logger.error(f"Failed to run FreeVC inference: {e}")
            return None
    
    def _convert_image_to_video(self, image_path: str, audio_path: str, output_path: str, duration: float = 5.0) -> bool:
        """
        이미지를 오디오 길이만큼 반복하여 비디오로 변환
        
        Args:
            image_path: 입력 이미지 경로
            audio_path: 참조 오디오 경로 (길이 확인용)
            output_path: 출력 비디오 경로
            duration: 최대 비디오 길이 (초)
            
        Returns:
            bool: 성공 여부
        """
        try:
            # librosa로 오디오 길이 확인
            import librosa
            audio_data, sr = librosa.load(audio_path, sr=None)
            audio_duration = len(audio_data) / sr
            
            # duration을 오디오 길이로 제한
            actual_duration = min(audio_duration, duration)
            
            # ffmpeg로 이미지를 비디오로 변환
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1",
                "-i", image_path,
                "-t", str(actual_duration),
                "-pix_fmt", "yuv420p",
                "-vf", "scale=640:480",
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"ffmpeg conversion failed: {result.stderr}")
                return False
            
            logger.info(f"Successfully converted image to video: {output_path} (duration: {actual_duration}s)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to convert image to video: {e}")
            return False

    async def run_wav2lip_inference(
        self,
        face_video_path: str,
        audio_path: str,
        output_gs_path: str,
        use_gpu: bool = True
    ) -> Optional[str]:
        """
        Wav2Lip 모델로 립싱크 영상 생성(GPU 버전)

        Args:
            face_video_path: 얼굴 영상 파일 경로 (로컬 또는 GCS) - 이미지 또는 비디오
            audio_path: 오디오 파일 경로 (로컬 또는 GCS)
            output_gs_path: 결과 영상을 업로드할 GCS 경로
            use_gpu: GPU 사용 여부 (True=CUDA, False=CPU)

        Returns:
            Optional[str]: 생성된 영상의 GCS 경로
        """
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                # 오디오 파일 처리 (로컬 또는 GCS)
                audio_local = os.path.join(tmp_dir, "audio.wav")
                if audio_path.startswith("gs://"):
                    if not self.gcs_client.download_file(audio_path, audio_local):
                        logger.error(f"Failed to download audio: {audio_path}")
                        return None
                else:
                    # 로컬 경로인 경우 복사
                    import shutil
                    shutil.copy2(audio_path, audio_local)
                    logger.info(f"Using local audio file: {audio_path}")
                
                # 얼굴 영상 파일 처리 (로컬 또는 GCS)
                face_local = os.path.join(tmp_dir, "face_input.mp4")
                input_local = os.path.join(tmp_dir, "input_file")
                
                if face_video_path.startswith("gs://"):
                    # GCS에서 다운로드
                    if not self.gcs_client.download_file(face_video_path, input_local):
                        logger.error(f"Failed to download face input: {face_video_path}")
                        return None
                else:
                    # 로컬 경로인 경우 복사
                    import shutil
                    shutil.copy2(face_video_path, input_local)
                    logger.info(f"Using local video file: {face_video_path}")
                
                # 파일 확장자 확인
                file_ext = os.path.splitext(input_local)[1].lower()
                if file_ext in ['.jpg', '.jpeg', '.png', '.bmp']:
                    # 이미지인 경우 비디오로 변환
                    logger.info(f"Converting image to video: {input_local}")
                    if not self._convert_image_to_video(input_local, audio_local, face_local):
                        logger.error("Failed to convert image to video")
                        return None
                else:
                    # 비디오인 경우 그대로 사용
                    os.rename(input_local, face_local)
                
                # 로컬 모델 파일 경로 설정
                model_local = os.path.join(settings.LOCAL_WAV2LIP_PATH, "checkpoints", "Wav2Lip_gan.pth")
                
                # 로컬 모델 파일 존재 확인
                if not os.path.exists(model_local):
                    logger.error(f"Wav2Lip model not found locally: {model_local}")
                    return None
                
                # 로컬 Wav2Lip 디렉토리 사용
                wav2lip_dir = settings.LOCAL_WAV2LIP_PATH
                
                # 로컬 Wav2Lip 파일들 존재 확인
                inference_path = os.path.join(wav2lip_dir, "inference.py")
                if not os.path.exists(inference_path):
                    logger.error(f"Wav2Lip inference script not found locally: {inference_path}")
                    return None
                
                # 출력 파일 경로 설정
                output_local = os.path.join(tmp_dir, "lipsynced.mp4")
                
                # Wav2Lip 추론 실행
                # CPU 모드에서는 메모리 절약을 위해 batch size를 작게 설정
                cmd = [
                    "python3", inference_path,
                    "--checkpoint_path", model_local,
                    "--face", face_local,
                    "--audio", audio_local,
                    "--outfile", output_local,
                    "--pads", "0", "20", "0", "0",
                    "--wav2lip_batch_size", "16",  # 8 → 16로 증가 (빠른 처리)
                    "--face_det_batch_size", "8",  # 4 → 8로 증가
                    "--resize_factor", "3",  # 2 → 3으로 증가 (640x360, 속도 우선)
                    "--nosmooth",  # Face detection smoothing 비활성화 (속도 향상)
                ]
                
                logger.info(f"Running Wav2Lip inference: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=wav2lip_dir)
                
                # 디버깅을 위한 상세 로그 출력
                logger.info(f"Wav2Lip return code: {result.returncode}")
                if result.stdout:
                    logger.info(f"Wav2Lip stdout:\n{result.stdout}")
                if result.stderr:
                    logger.info(f"Wav2Lip stderr:\n{result.stderr}")
                
                # Return code 먼저 체크
                if result.returncode != 0:
                    logger.error(f"Wav2Lip inference failed with return code {result.returncode}")
                    logger.error(f"stdout: {result.stdout}")
                    logger.error(f"stderr: {result.stderr}")
                    logger.error(f"Temporary directory contents: {os.listdir(tmp_dir)}")
                    return None
                
                # 출력 파일 존재 확인
                if not os.path.exists(output_local):
                    logger.error(f"Wav2Lip output file not found: {output_local}")
                    logger.error(f"Temporary directory contents: {os.listdir(tmp_dir)}")
                    logger.error(f"stdout: {result.stdout}")
                    logger.error(f"stderr: {result.stderr}")
                    return None
                
                # 결과 파일을 사용자 지정 GCS 경로로 직접 업로드
                logger.info(f"Uploading Wav2Lip output to GCS: {output_local} -> {output_gs_path}")
                if not self.gcs_client.upload_file(output_local, output_gs_path):
                    logger.error("Failed to upload Wav2Lip output to GCS")
                    return None
                    
                logger.info(f"Wav2Lip inference completed: {output_gs_path}")
                return output_gs_path
                    
        except Exception as e:
            logger.error(f"Failed to run Wav2Lip inference: {e}")
            return None

# 전역 AI 서비스 인스턴스
ai_service = AIService()
