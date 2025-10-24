import os
import subprocess
import tempfile
import time
from typing import Optional, Tuple
from api.utils.gcs_client import gcs_client
from api.core.config import settings
import logging

logger = logging.getLogger(__name__)


class AIService:
    """AI 모델 서비스 클래스"""
    
    def __init__(self):
        self.gcs_client = gcs_client
    
    async def generate_tts_audio(self, text: str, lang: str = "ko") -> Optional[str]:
        """
        TTS로 오디오 생성
        
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
                # Google Cloud TTS 사용
                from google.cloud import texttospeech
                
                client = texttospeech.TextToSpeechClient()
                
                # 입력 텍스트 설정
                synthesis_input = texttospeech.SynthesisInput(text=text)
                
                # 음성 설정
                voice = texttospeech.VoiceSelectionParams(
                    language_code=lang,
                    ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL,
                )
                
                # 오디오 설정
                audio_config = texttospeech.AudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.LINEAR16,
                    sample_rate_hertz=22050,
                )
                
                # TTS 실행
                response = client.synthesize_speech(
                    input=synthesis_input,
                    voice=voice,
                    audio_config=audio_config
                )
                
                # 임시 파일에 저장
                with open(tmp_path, "wb") as out:
                    out.write(response.audio_content)
                
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
                # GCS에서 파일 다운로드
                src_local = os.path.join(tmp_dir, "src_audio.wav")
                ref_local = os.path.join(tmp_dir, "ref_audio.wav")
                
                if not self.gcs_client.download_file(src_audio_path, src_local):
                    logger.error(f"Failed to download src audio: {src_audio_path}")
                    return None
                
                if not self.gcs_client.download_file(ref_audio_path, ref_local):
                    logger.error(f"Failed to download ref audio: {ref_audio_path}")
                    return None
                
                # 모델 파일 다운로드
                model_local = os.path.join(tmp_dir, "freevc-s.pth")
                config_local = os.path.join(tmp_dir, "freevc-s.json")
                
                model_gs = self.gcs_client.get_model_path("freevc-s.pth")
                config_gs = self.gcs_client.get_model_path("freevc-s.json")
                
                if not self.gcs_client.download_file(model_gs, model_local):
                    logger.error(f"Failed to download FreeVC model: {model_gs}")
                    return None
                
                if not self.gcs_client.download_file(config_gs, config_local):
                    logger.error(f"Failed to download FreeVC config: {config_gs}")
                    return None
                
                # 출력 파일 경로 설정
                output_local = os.path.join(tmp_dir, "freevc_out.wav")
                
                # FreeVC 추론 실행
                cmd = [
                    "python", "freevc_infer.py",
                    "--hpfile", config_local,
                    "--ptfile", model_local,
                    "--src_audio", src_local,
                    "--ref_audio", ref_local,
                    "--out", output_local,
                    "--outdir", tmp_dir,
                    "--use_timestamp"
                ]
                
                logger.info(f"Running FreeVC inference: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=settings.FREEVC_SDK_PATH)
                
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
    
    async def run_wav2lip_inference(
        self,
        face_video_path: str,
        audio_path: str,
        output_prefix: str
    ) -> Optional[str]:
        """
        Wav2Lip 모델로 립싱크 영상 생성
        
        Args:
            face_video_path: 얼굴 영상 파일 경로 (GCS)
            audio_path: 오디오 파일 경로 (GCS)
            output_prefix: 출력 파일명 접두사
            
        Returns:
            Optional[str]: 생성된 영상의 GCS 경로
        """
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                # GCS에서 파일 다운로드
                face_local = os.path.join(tmp_dir, "face_video.mp4")
                audio_local = os.path.join(tmp_dir, "audio.wav")
                
                if not self.gcs_client.download_file(face_video_path, face_local):
                    logger.error(f"Failed to download face video: {face_video_path}")
                    return None
                
                if not self.gcs_client.download_file(audio_path, audio_local):
                    logger.error(f"Failed to download audio: {audio_path}")
                    return None
                
                # 모델 파일 다운로드
                model_local = os.path.join(tmp_dir, "Wav2Lip_gan.pth")
                model_gs = self.gcs_client.get_model_path("Wav2Lip_gan.pth")
                
                if not self.gcs_client.download_file(model_gs, model_local):
                    logger.error(f"Failed to download Wav2Lip model: {model_gs}")
                    return None
                
                # 출력 파일 경로 설정
                output_local = os.path.join(tmp_dir, "lipsynced.mp4")
                
                # Wav2Lip 추론 실행
                cmd = [
                    "python", "inference.py",
                    "--checkpoint_path", model_local,
                    "--face", face_local,
                    "--audio", audio_local,
                    "--outfile", output_local,
                    "--pads", "0", "20", "0", "0",
                    "--wav2lip_batch_size", "32"
                ]
                
                logger.info(f"Running Wav2Lip inference: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=settings.W2L_SDK_PATH)
                
                if result.returncode != 0:
                    logger.error(f"Wav2Lip inference failed: {result.stderr}")
                    return None
                
                # 결과 파일을 GCS에 업로드
                output_gs_path = f"gs://{settings.GCS_BUCKET}/{settings.PREFIX_W2L}/{output_prefix}_lipsynced.mp4"
                
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
