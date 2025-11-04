import subprocess
import os
import tempfile
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path
from google.cloud import storage
from api.core.config import settings
import aiofiles
from api.src.train.services.praat import extract_all_features


class VideoProcessor:
    """FFmpeg를 사용한 동영상 처리 서비스"""
    
    def __init__(self):
        self.gcs_client = storage.Client(project=settings.GCS_PROJECT_ID)
    
    async def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """동영상 메타데이터 추출"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', file_path
            ]
            
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode != 0:
                raise Exception(f"FFprobe error: {stderr.decode()}")
            
            import json
            metadata = json.loads(stdout.decode())
            
            # 비디오 스트림 정보 추출
            video_stream = None
            for stream in metadata.get('streams', []):
                if stream.get('codec_type') == 'video':
                    video_stream = stream
                    break
            
            if not video_stream:
                raise Exception("No video stream found")
            
            return {
                'duration_ms': int(float(metadata['format']['duration']) * 1000),
                'width_px': video_stream.get('width'),
                'height_px': video_stream.get('height'),
                'codec': video_stream.get('codec_name'),
                'bitrate': metadata['format'].get('bit_rate'),
                'fps': eval(video_stream.get('r_frame_rate', '0/1'))
            }
            
        except Exception as e:
            raise Exception(f"Metadata extraction failed: {str(e)}")
    
    async def generate_thumbnail(
        self, 
        input_path: str, 
        output_path: str, 
        timestamp: float = 1.0
    ) -> bool:
        """썸네일 생성"""
        try:
            cmd = [
                'ffmpeg', '-i', input_path,
                '-ss', str(timestamp),  # 특정 시점
                '-vframes', '1',        # 1프레임만
                '-vf', 'scale=320:240',  # 썸네일 크기
                '-y',                    # 덮어쓰기
                output_path
            ]
            
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode != 0:
                raise Exception(f"Thumbnail generation failed: {stderr.decode()}")
            
            return True
            
        except Exception as e:
            raise Exception(f"Thumbnail generation failed: {str(e)}")
    
    async def process_uploaded_video(
        self, 
        gcs_bucket: str, 
        gcs_blob_name: str
    ) -> Dict[str, Any]:
        """업로드된 동영상 처리"""
        try:
            # 임시 디렉토리 생성
            with tempfile.TemporaryDirectory() as temp_dir:
                # GCS에서 파일 다운로드
                bucket = self.gcs_client.bucket(gcs_bucket)
                blob = bucket.blob(gcs_blob_name)
                
                input_path = os.path.join(temp_dir, "input.mp4")
                blob.download_to_filename(input_path)
                
                # 메타데이터 추출
                metadata = await self.extract_metadata(input_path)
                
                # 썸네일 생성
                thumbnail_path = os.path.join(temp_dir, "thumbnail.jpg")
                await self.generate_thumbnail(input_path, thumbnail_path)
                
                # 썸네일을 GCS에 업로드
                thumbnail_blob_name = gcs_blob_name.replace('.mp4', '_thumb.jpg')
                thumbnail_blob = bucket.blob(thumbnail_blob_name)
                thumbnail_blob.upload_from_filename(thumbnail_path)
                
                return {
                    'metadata': metadata,
                    'thumbnail_url': f"gs://{gcs_bucket}/{thumbnail_blob_name}"
                }
                
        except Exception as e:
            raise Exception(f"Video processing failed: {str(e)}")
    
    async def extract_stereo_audio(
        self, 
        input_path: str, 
        output_path: str
    ) -> bool:
        """동영상에서 스테레오 음성을 WAV 형식으로 추출"""
        try:
            cmd = [
                'ffmpeg', '-i', input_path,
                '-vn',                    # 비디오 스트림 제외
                '-ac', '2',               # 스테레오 (2채널)
                '-ar', '44100',           # 샘플링 레이트 44.1kHz
                '-acodec', 'pcm_s16le',   # 16-bit PCM 인코딩
                '-y',                     # 덮어쓰기
                output_path
            ]
            
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode != 0:
                raise Exception(f"Audio extraction failed: {stderr.decode()}")
            
            return True
            
        except Exception as e:
            raise Exception(f"Audio extraction failed: {str(e)}")
    
    async def process_uploaded_video_with_audio(
        self, 
        gcs_bucket: str, 
        gcs_blob_name: str
    ) -> Dict[str, Any]:
        """업로드된 동영상 처리 (메타데이터, 썸네일, 음성 추출)"""
        try:
            # 임시 디렉토리 생성
            with tempfile.TemporaryDirectory() as temp_dir:
                # GCS에서 파일 다운로드
                bucket = self.gcs_client.bucket(gcs_bucket)
                blob = bucket.blob(gcs_blob_name)
                
                input_path = os.path.join(temp_dir, "input.mp4")
                blob.download_to_filename(input_path)
                
                # 메타데이터 추출
                metadata = await self.extract_metadata(input_path)
                
                # 썸네일 생성
                thumbnail_path = os.path.join(temp_dir, "thumbnail.jpg")
                await self.generate_thumbnail(input_path, thumbnail_path)
                
                # 음성 추출
                audio_path = os.path.join(temp_dir, "audio.wav")
                await self.extract_stereo_audio(input_path, audio_path)
                
                # praat 추출
                praat_results = None  # 결과 초기화
                try:
                    # 1. 로컬에 생성된 .wav 파일을 바이트로 읽기
                    async with aiofiles.open(audio_path, 'rb') as f:
                        wav_bytes = await f.read()
                    # 2. 읽은 파일을 praat 추출
                    praat_results = await extract_all_features(wav_bytes) 

                    
                except Exception as e:
                    print(f"Praat analysis failed: {str(e)}")
                    # Praat 분석이 실패해도 나머지 작업은 계속 진행

                # 썸네일을 GCS에 업로드
                thumbnail_blob_name = gcs_blob_name.replace('.mp4', '_thumb.jpg')
                thumbnail_blob = bucket.blob(thumbnail_blob_name)
                thumbnail_blob.upload_from_filename(thumbnail_path)
                
                # 음성 파일을 GCS에 업로드
                audio_blob_name = gcs_blob_name.replace('.mp4', '.wav')
                audio_blob = bucket.blob(audio_blob_name)
                audio_blob.upload_from_filename(audio_path)
                
                return {
                    'metadata': metadata,
                    'thumbnail_url': f"gs://{gcs_bucket}/{thumbnail_blob_name}",
                    'audio_url': f"gs://{gcs_bucket}/{audio_blob_name}",
                    'audio_blob_name': audio_blob_name,
                    'praat_features': praat_results
                }
                
        except Exception as e:
            raise Exception(f"Video processing with audio extraction failed: {str(e)}")

    def check_ffmpeg_availability(self) -> bool:
        """FFmpeg 사용 가능 여부 확인"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
