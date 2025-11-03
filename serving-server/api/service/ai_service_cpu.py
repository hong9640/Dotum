import os
import subprocess
import tempfile
import time
from typing import Optional, Tuple
from api.utils.gcs_client import gcs_client
from api.core.config import settings
from api.core.logger import logger, log_step, log_success, log_error


class AIService:
    """AI 모델 서비스 클래스"""
    
    def __init__(self):
        self.gcs_client = gcs_client
    
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

    async def extract_audio_from_video(self, video_gs_path: str) -> Optional[str]:
        """
        영상에서 오디오 추출
        
        Args:
            video_gs_path: GCS 영상 경로
            
        Returns:
            Optional[str]: 추출된 오디오의 로컬 경로
        """
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                # GCS에서 영상 다운로드
                video_local = os.path.join(tmp_dir, "input_video.mp4")
                if not self.gcs_client.download_file(video_gs_path, video_local):
                    logger.error(f"Failed to download video: {video_gs_path}")
                    return None
                
                # 오디오 추출
                audio_local = os.path.join(tmp_dir, "extracted_audio.wav")
                cmd = [
                    "ffmpeg", "-y",
                    "-i", video_local,
                    "-vn",  # 비디오 스트림 제거
                    "-acodec", "pcm_s16le",  # 오디오 코덱
                    "-ar", "16000",  # 샘플레이트
                    "-ac", "1",  # 모노
                    audio_local
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.error(f"Failed to extract audio: {result.stderr}")
                    return None
                
                # 추출된 오디오를 임시 저장 (삭제되지 않도록)
                persistent_audio = f"/tmp/extracted_audio_{int(time.time())}.wav"
                import shutil
                shutil.copy2(audio_local, persistent_audio)
                
                logger.info(f"Audio extracted from video: {persistent_audio}")
                return persistent_audio
                
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
                
                convert_cpu_path = os.path.join(freevc_dir, "convert_cpu.py")
                if not os.path.exists(convert_cpu_path):
                    logger.error(f"FreeVC CPU convert script not found locally: {convert_cpu_path}")
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
        output_prefix: str
    ) -> Optional[str]:
        """
        Wav2Lip 모델로 립싱크 영상 생성
        
        Args:
            face_video_path: 얼굴 영상 파일 경로 (GCS) - 이미지 또는 비디오
            audio_path: 오디오 파일 경로 (로컬 또는 GCS)
            output_prefix: 출력 파일명 접두사
            
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
                
                # GCS에서 얼굴 입력 파일 다운로드
                face_local = os.path.join(tmp_dir, "face_input.mp4")
                input_local = os.path.join(tmp_dir, "input_file")
                if not self.gcs_client.download_file(face_video_path, input_local):
                    logger.error(f"Failed to download face input: {face_video_path}")
                    return None
                
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
                
                # 필수 파일들 존재 확인
                essential_files = [
                    "audio.py", "hparams.py", "preprocess.py"
                ]
                
                for filename in essential_files:
                    file_path = os.path.join(wav2lip_dir, filename)
                    if not os.path.exists(file_path):
                        logger.error(f"Wav2Lip essential file not found locally: {file_path}")
                        return None
                
                # 하위 디렉토리들 존재 확인
                required_dirs = [
                    "models", "face_detection", "face_detection/detection", "face_detection/detection/sfd"
                ]
                
                for dir_name in required_dirs:
                    dir_path = os.path.join(wav2lip_dir, dir_name)
                    if not os.path.exists(dir_path):
                        logger.error(f"Wav2Lip directory not found locally: {dir_path}")
                        return None
                
                # 출력 파일 경로 설정
                output_local = os.path.join(tmp_dir, "lipsynced.mp4")
                
                # Wav2Lip 추론 실행 (메모리 최적화를 위해 배치 크기 감소)
                cmd = [
                    "python3", inference_path,
                    "--checkpoint_path", model_local,
                    "--face", face_local,
                    "--audio", audio_local,
                    "--outfile", output_local,
                    "--pads", "0", "20", "0", "0",
                    "--wav2lip_batch_size", "1",
                    "--static", "False",
                    "--fps", "25"
                ]
                
                logger.info(f"Running Wav2Lip inference: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=wav2lip_dir)
                
                # 디버깅을 위한 로그 출력
                logger.info(f"Wav2Lip return code: {result.returncode}")
                if result.stdout:
                    logger.info(f"Wav2Lip stdout: {result.stdout}")
                if result.stderr:
                    logger.warning(f"Wav2Lip stderr: {result.stderr}")
                
                # 출력 파일 존재 확인
                if not os.path.exists(output_local):
                    logger.error(f"Wav2Lip output file not found: {output_local}")
                    logger.error(f"Temporary directory contents: {os.listdir(tmp_dir)}")
                    if result.stderr:
                        logger.error(f"Wav2Lip error details: {result.stderr}")
                    return None
                
                if result.returncode != 0:
                    logger.error(f"Wav2Lip inference failed with return code {result.returncode}: {result.stderr}")
                    return None
                
                # 결과 파일을 GCS에 업로드
                output_gs_path = f"gs://{settings.GCS_BUCKET}/{settings.PREFIX_W2L}/{output_prefix}_lipsynced.mp4"
                
                logger.info(f"Uploading Wav2Lip output to GCS: {output_local} -> {output_gs_path}")
                if self.gcs_client.upload_file(output_local, output_gs_path):
                    logger.info(f"Wav2Lip inference completed: {output_gs_path}")
                    
                    # 캐시 파일들 정리
                    cache_files_to_clean = [
                        audio_path if not audio_path.startswith("gs://") else None,
                        f"/tmp/{output_prefix}_freevc_out.wav" if output_prefix else None
                    ]
                    
                    for cache_file in cache_files_to_clean:
                        if cache_file and os.path.exists(cache_file):
                            try:
                                os.unlink(cache_file)
                                logger.info(f"Cleaned up cache file: {cache_file}")
                            except Exception as e:
                                logger.warning(f"Failed to clean up cache file {cache_file}: {e}")
                    
                    return output_gs_path
                else:
                    logger.error("Failed to upload Wav2Lip output to GCS")
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to run Wav2Lip inference: {e}")
            return None

# 전역 AI 서비스 인스턴스
ai_service = AIService()
