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
            Optional[str]: 생성된 TTS 오디오의 GCS 경로
        """
        try:
            # TTS 파일명 생성 (텍스트 해시 기반)
            import hashlib
            text_hash = hashlib.md5(text.encode()).hexdigest()
            tts_filename = f"{text_hash}_{lang}.wav"
            tts_gs_path = f"gs://{settings.GCS_BUCKET}/{settings.PREFIX_TTS}/{tts_filename}"
            
            # 이미 TTS 파일이 존재하는지 확인
            if self.gcs_client.file_exists(tts_gs_path):
                logger.info(f"TTS file already exists: {tts_gs_path}")
                return tts_gs_path
            
            # 임시 파일 경로 생성
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                tmp_path = tmp_file.name
            
            try:
                # gTTS 사용
                from gtts import gTTS
                
                # gTTS 객체 생성
                tts = gTTS(text=text, lang=lang, slow=False)
                
                # 임시 파일에 저장
                tts.save(tmp_path)
                
                # GCS에 업로드
                if self.gcs_client.upload_file(tmp_path, tts_gs_path):
                    logger.info(f"TTS generated successfully: {tts_gs_path}")
                    return tts_gs_path
                else:
                    logger.error("Failed to upload TTS file to GCS")
                    return None
                    
            finally:
                # 임시 파일 정리
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    
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
            src_audio_path: 원본 오디오 파일 경로 (GCS)
            ref_audio_path: 참조 오디오 파일 경로 (GCS)
            output_prefix: 출력 파일명 접두사
            
        Returns:
            Optional[str]: 생성된 오디오의 GCS 경로
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
                
                # ref_audio_path는 항상 GCS 경로
                if not self.gcs_client.download_file(ref_audio_path, ref_local):
                    logger.error(f"Failed to download ref audio: {ref_audio_path}")
                    return None
                
                # 모델 파일 다운로드
                model_local = os.path.join(tmp_dir, "freevc-s.pth")
                config_local = os.path.join(tmp_dir, "freevc-s.json")
                
                model_gs = f"gs://{settings.GCS_BUCKET}/{settings.FREEVC_MODEL_PATH}/checkpoints/freevc-s.pth"
                config_gs = f"gs://{settings.GCS_BUCKET}/{settings.FREEVC_MODEL_PATH}/configs/freevc-s.json"
                
                if not self.gcs_client.download_file(model_gs, model_local):
                    logger.error(f"Failed to download FreeVC model: {model_gs}")
                    return None
                
                if not self.gcs_client.download_file(config_gs, config_local):
                    logger.error(f"Failed to download FreeVC config: {config_gs}")
                    return None
                
                # 출력 파일 경로 설정
                output_local = os.path.join(tmp_dir, "freevc_out.wav")
                
                # FreeVC 디렉토리 생성
                freevc_dir = os.path.join(tmp_dir, "FreeVC")
                os.makedirs(freevc_dir, exist_ok=True)
                
                # FreeVC 실행 파일 다운로드
                freevc_infer_path = os.path.join(freevc_dir, "freevc_infer.py")
                if not self.gcs_client.download_file(f"gs://{settings.GCS_BUCKET}/{settings.FREEVC_MODEL_PATH}/freevc_infer.py", freevc_infer_path):
                    logger.error("Failed to download FreeVC inference script")
                    return None
                
                # CPU 모드 convert.py 다운로드
                convert_cpu_path = os.path.join(freevc_dir, "convert.py")
                if not self.gcs_client.download_file(f"gs://{settings.GCS_BUCKET}/{settings.FREEVC_MODEL_PATH}/convert_cpu.py", convert_cpu_path):
                    logger.error("Failed to download CPU mode convert script")
                    return None
                
                # FreeVC의 다른 필요한 파일들 다운로드 (CPU 모드 우선)
                essential_files = [
                    ("convert_cpu.py", "convert.py"),  # CPU 모드 파일을 원본 이름으로 저장
                    "commons.py", "data_utils.py", "downsample.py",
                    "losses.py", "mel_processing.py", "models.py", "modules.py",
                    ("utils_cpu.py", "utils.py"),  # CPU 모드 파일
                    "preprocess_flist.py", "preprocess_spk.py",
                    ("preprocess_sr_cpu.py", "preprocess_sr.py"),  # CPU 모드 파일
                    ("preprocess_ssl_cpu.py", "preprocess_ssl.py"),  # CPU 모드 파일
                    "train.py"
                ]
                
                for file_info in essential_files:
                    if isinstance(file_info, tuple):
                        gcs_filename, local_filename = file_info
                    else:
                        gcs_filename = local_filename = file_info
                    
                    gcs_path = f"gs://{settings.GCS_BUCKET}/{settings.FREEVC_MODEL_PATH}/{gcs_filename}"
                    local_path = os.path.join(freevc_dir, local_filename)
                    if self.gcs_client.file_exists(gcs_path):
                        self.gcs_client.download_file(gcs_path, local_path)
                        logger.info(f"Downloaded {gcs_filename} as {local_filename}")
                
                # hifigan 디렉토리 다운로드
                hifigan_dir = os.path.join(freevc_dir, "hifigan")
                os.makedirs(hifigan_dir, exist_ok=True)
                
                hifigan_files = ["__init__.py", "models.py"]
                for filename in hifigan_files:
                    gcs_path = f"gs://{settings.GCS_BUCKET}/{settings.FREEVC_MODEL_PATH}/hifigan/{filename}"
                    local_path = os.path.join(hifigan_dir, filename)
                    if self.gcs_client.file_exists(gcs_path):
                        self.gcs_client.download_file(gcs_path, local_path)
                        logger.info(f"Downloaded hifigan/{filename}")
                
                # speaker_encoder 디렉토리 다운로드
                speaker_encoder_dir = os.path.join(freevc_dir, "speaker_encoder")
                os.makedirs(speaker_encoder_dir, exist_ok=True)
                
                speaker_encoder_files = [
                    "__init__.py", "audio.py", "compute_embed.py", "config.py",
                    "hparams.py", "inference.py", "model.py", "params_data.py",
                    "params_model.py", "preprocess.py", "train.py", "voice_encoder.py"
                ]
                
                for filename in speaker_encoder_files:
                    gcs_path = f"gs://{settings.GCS_BUCKET}/{settings.FREEVC_MODEL_PATH}/speaker_encoder/{filename}"
                    local_path = os.path.join(speaker_encoder_dir, filename)
                    if self.gcs_client.file_exists(gcs_path):
                        self.gcs_client.download_file(gcs_path, local_path)
                        logger.info(f"Downloaded speaker_encoder/{filename}")
                
                # data_objects 디렉토리 다운로드
                data_objects_dir = os.path.join(speaker_encoder_dir, "data_objects")
                os.makedirs(data_objects_dir, exist_ok=True)
                
                data_objects_files = [
                    "__init__.py", "random_cycler.py", "speaker.py",
                    "speaker_batch.py", "speaker_verification_dataset.py", "utterance.py"
                ]
                
                for filename in data_objects_files:
                    gcs_path = f"gs://{settings.GCS_BUCKET}/{settings.FREEVC_MODEL_PATH}/speaker_encoder/data_objects/{filename}"
                    local_path = os.path.join(data_objects_dir, filename)
                    if self.gcs_client.file_exists(gcs_path):
                        self.gcs_client.download_file(gcs_path, local_path)
                        logger.info(f"Downloaded speaker_encoder/data_objects/{filename}")
                
                # wavlm 디렉토리 다운로드
                wavlm_dir = os.path.join(freevc_dir, "wavlm")
                os.makedirs(wavlm_dir, exist_ok=True)
                
                wavlm_files = ["__init__.py", "modules.py", "WavLM.py", "WavLM-Large.pt"]
                for filename in wavlm_files:
                    gcs_path = f"gs://{settings.GCS_BUCKET}/{settings.FREEVC_MODEL_PATH}/wavlm/{filename}"
                    local_path = os.path.join(wavlm_dir, filename)
                    if self.gcs_client.file_exists(gcs_path):
                        self.gcs_client.download_file(gcs_path, local_path)
                        logger.info(f"Downloaded wavlm/{filename}")
                
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
                
                # 결과 파일을 GCS에 업로드
                output_gs_path = f"gs://{settings.GCS_BUCKET}/{settings.PREFIX_FREEVC}/{output_prefix}_freevc_out.wav"
                
                if self.gcs_client.upload_file(output_local, output_gs_path):
                    logger.info(f"FreeVC inference completed: {output_gs_path}")
                    return output_gs_path
                else:
                    logger.error("Failed to upload FreeVC output to GCS")
                    return None
                    
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
            audio_path: 오디오 파일 경로 (GCS)
            output_prefix: 출력 파일명 접두사
            
        Returns:
            Optional[str]: 생성된 영상의 GCS 경로
        """
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                # GCS에서 오디오 파일 먼저 다운로드
                audio_local = os.path.join(tmp_dir, "audio.wav")
                if not self.gcs_client.download_file(audio_path, audio_local):
                    logger.error(f"Failed to download audio: {audio_path}")
                    return None
                
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
                
                # 모델 파일 다운로드
                model_local = os.path.join(tmp_dir, "Wav2Lip_gan.pth")
                model_gs = f"gs://{settings.GCS_BUCKET}/{settings.WAV2LIP_MODEL_PATH}/checkpoints/Wav2Lip_gan.pth"
                
                if not self.gcs_client.download_file(model_gs, model_local):
                    logger.error(f"Failed to download Wav2Lip model: {model_gs}")
                    return None
                
                # Wav2Lip 디렉토리 생성
                wav2lip_dir = os.path.join(tmp_dir, "Wav2Lip")
                os.makedirs(wav2lip_dir, exist_ok=True)
                
                # Wav2Lip에서 사용하는 temp 디렉토리 생성
                temp_dir = os.path.join(wav2lip_dir, "temp")
                os.makedirs(temp_dir, exist_ok=True)
                
                # Wav2Lip 실행 파일 다운로드
                inference_path = os.path.join(wav2lip_dir, "inference.py")
                if not self.gcs_client.download_file(f"gs://{settings.GCS_BUCKET}/{settings.WAV2LIP_MODEL_PATH}/inference.py", inference_path):
                    logger.error("Failed to download Wav2Lip inference script")
                    return None
                
                # Wav2Lip의 다른 필요한 파일들 다운로드
                essential_files = [
                    "audio.py", "hparams.py", "preprocess.py"
                ]
                
                for filename in essential_files:
                    gcs_path = f"gs://{settings.GCS_BUCKET}/{settings.WAV2LIP_MODEL_PATH}/{filename}"
                    local_path = os.path.join(wav2lip_dir, filename)
                    if self.gcs_client.file_exists(gcs_path):
                        self.gcs_client.download_file(gcs_path, local_path)
                        logger.info(f"Downloaded {filename}")
                
                # models 디렉토리 다운로드
                models_dir = os.path.join(wav2lip_dir, "models")
                os.makedirs(models_dir, exist_ok=True)
                
                models_files = ["__init__.py", "conv.py", "syncnet.py", "wav2lip.py"]
                for filename in models_files:
                    gcs_path = f"gs://{settings.GCS_BUCKET}/{settings.WAV2LIP_MODEL_PATH}/models/{filename}"
                    local_path = os.path.join(models_dir, filename)
                    if self.gcs_client.file_exists(gcs_path):
                        self.gcs_client.download_file(gcs_path, local_path)
                        logger.info(f"Downloaded models/{filename}")
                
                # face_detection 디렉토리 다운로드
                face_detection_dir = os.path.join(wav2lip_dir, "face_detection")
                os.makedirs(face_detection_dir, exist_ok=True)
                
                face_detection_files = [
                    "__init__.py", "api.py", "models.py", "utils.py"
                ]
                for filename in face_detection_files:
                    gcs_path = f"gs://{settings.GCS_BUCKET}/{settings.WAV2LIP_MODEL_PATH}/face_detection/{filename}"
                    local_path = os.path.join(face_detection_dir, filename)
                    if self.gcs_client.file_exists(gcs_path):
                        self.gcs_client.download_file(gcs_path, local_path)
                        logger.info(f"Downloaded face_detection/{filename}")
                
                # detection 서브디렉토리 다운로드
                detection_dir = os.path.join(face_detection_dir, "detection")
                os.makedirs(detection_dir, exist_ok=True)
                
                detection_files = ["__init__.py", "core.py"]
                for filename in detection_files:
                    gcs_path = f"gs://{settings.GCS_BUCKET}/{settings.WAV2LIP_MODEL_PATH}/face_detection/detection/{filename}"
                    local_path = os.path.join(detection_dir, filename)
                    if self.gcs_client.file_exists(gcs_path):
                        self.gcs_client.download_file(gcs_path, local_path)
                        logger.info(f"Downloaded face_detection/detection/{filename}")
                
                # sfd 서브디렉토리 다운로드
                sfd_dir = os.path.join(detection_dir, "sfd")
                os.makedirs(sfd_dir, exist_ok=True)
                
                sfd_files = ["__init__.py", "bbox.py", "detect.py", "net_s3fd.py", "sfd_detector.py"]
                for filename in sfd_files:
                    gcs_path = f"gs://{settings.GCS_BUCKET}/{settings.WAV2LIP_MODEL_PATH}/face_detection/detection/sfd/{filename}"
                    local_path = os.path.join(sfd_dir, filename)
                    if self.gcs_client.file_exists(gcs_path):
                        self.gcs_client.download_file(gcs_path, local_path)
                        logger.info(f"Downloaded face_detection/detection/sfd/{filename}")
                
                # 출력 파일 경로 설정
                output_local = os.path.join(tmp_dir, "lipsynced.mp4")
                
                # Wav2Lip 추론 실행
                cmd = [
                    "python3", inference_path,
                    "--checkpoint_path", model_local,
                    "--face", face_local,
                    "--audio", audio_local,
                    "--outfile", output_local,
                    "--pads", "0", "20", "0", "0",
                    "--wav2lip_batch_size", "32"
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
                    return output_gs_path
                else:
                    logger.error("Failed to upload Wav2Lip output to GCS")
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to run Wav2Lip inference: {e}")
            return None

# 전역 AI 서비스 인스턴스
ai_service = AIService()
