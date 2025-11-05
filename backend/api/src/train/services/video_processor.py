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
            
            # duration이 없는 경우 대비
            duration_ms = 0
            if 'duration' in metadata.get('format', {}):
                duration_ms = int(float(metadata['format']['duration']) * 1000)
            
            return {
                'duration_ms': duration_ms,
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
            # FFmpeg 설치 확인
            if not self.check_ffmpeg_availability():
                raise Exception("FFmpeg가 설치되어 있지 않습니다. 'sudo apt-get install ffmpeg' 명령으로 설치하세요.")
            
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
                error_msg = stderr.decode()
                print(f"[WAV] FFmpeg 에러: {error_msg}")
                raise Exception(f"Audio extraction failed: {error_msg}")
            
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
                
                # 메타데이터 추출 (선택적 - 실패해도 계속 진행)
                metadata = {}
                try:
                    metadata = await self.extract_metadata(input_path)
                    print(f"[WAV] 메타데이터 추출 완료")
                except Exception as e:
                    print(f"[WAV] 메타데이터 추출 실패 (무시하고 계속): {str(e)}")
                
                # 썸네일 생성 (선택적 - 실패해도 계속 진행)
                thumbnail_path = os.path.join(temp_dir, "thumbnail.jpg")
                thumbnail_success = False
                try:
                    await self.generate_thumbnail(input_path, thumbnail_path)
                    thumbnail_success = True
                    print(f"[WAV] 썸네일 생성 완료")
                except Exception as e:
                    print(f"[WAV] 썸네일 생성 실패 (무시하고 계속): {str(e)}")
                
                # 음성 추출 (필수)
                audio_path = os.path.join(temp_dir, "audio.wav")
                print(f"[WAV] 음성 추출 시작: {gcs_blob_name}")
                await self.extract_stereo_audio(input_path, audio_path)
                
                # WAV 파일 생성 확인
                if os.path.exists(audio_path):
                    audio_size = os.path.getsize(audio_path)
                    print(f"[WAV] 음성 파일 생성 완료: {audio_size:,} bytes")
                else:
                    print(f"[WAV] 에러: 음성 파일이 생성되지 않음")
                    raise Exception(f"WAV 파일 생성 실패: {audio_path}")
                
                # praat 추출
                praat_results = None  # 결과 초기화
                try:
                    print(f"[WAV] Praat 분석 시작")
                    # 1. 로컬에 생성된 .wav 파일을 바이트로 읽기
                    async with aiofiles.open(audio_path, 'rb') as f:
                        wav_bytes = await f.read()
                    # 2. 읽은 파일을 praat 추출
                    praat_results = await extract_all_features(wav_bytes) 
                    print(f"[WAV] Praat 분석 완료")
                    
                except Exception as e:
                    print(f"[WAV] Praat analysis failed: {str(e)}")
                    # Praat 분석이 실패해도 나머지 작업은 계속 진행

                # 썸네일을 GCS에 업로드 (성공한 경우에만)
                thumbnail_blob_name = None
                if thumbnail_success:
                    try:
                        thumbnail_blob_name = gcs_blob_name.replace('.mp4', '_thumb.jpg')
                        thumbnail_blob = bucket.blob(thumbnail_blob_name)
                        thumbnail_blob.upload_from_filename(thumbnail_path)
                        print(f"[WAV] 썸네일 업로드 완료")
                    except Exception as e:
                        print(f"[WAV] 썸네일 업로드 실패 (무시하고 계속): {str(e)}")
                        thumbnail_blob_name = None
                
                # 음성 파일을 GCS에 업로드 (필수)
                audio_blob_name = gcs_blob_name.replace('.mp4', '.wav')
                audio_blob = bucket.blob(audio_blob_name)
                print(f"[WAV] GCS 업로드 시작: {audio_blob_name}")
                audio_blob.upload_from_filename(audio_path)
                print(f"[WAV] GCS 업로드 완료: gs://{gcs_bucket}/{audio_blob_name}")
                
                return {
                    'metadata': metadata,
                    'thumbnail_url': f"gs://{gcs_bucket}/{thumbnail_blob_name}" if thumbnail_blob_name else None,
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

    async def convert_mp3_to_wav(self, mp3_bytes: bytes) -> bytes:
        """
        MP3 바이트 데이터를 입력받아 WAV 바이트 데이터로 변환합니다.
        FFmpeg를 사용하여 인메모리 방식으로 처리합니다.
        """
        if not self.check_ffmpeg_availability():
            raise Exception("FFmpeg가 설치되어 있지 않습니다.")

        temp_mp3_path = None
        temp_wav_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_mp3, \
                 tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:

                temp_mp3_path = temp_mp3.name
                temp_wav_path = temp_wav.name

                async with aiofiles.open(temp_mp3_path, 'wb') as f:
                    await f.write(mp3_bytes)

                cmd = [
                    'ffmpeg', '-i', temp_mp3_path,
                    '-acodec', 'pcm_s16le',   # 16-bit PCM WAV
                    '-ar', '44100',           # 샘플링 레이트
                    '-ac', '1',               # 모노 채널
                    '-y',                     # 덮어쓰기
                    temp_wav_path
                ]

                process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
                _, stderr = await process.communicate()

                if process.returncode != 0:
                    raise Exception(f"MP3 to WAV 변환 실패: {stderr.decode()}")

                async with aiofiles.open(temp_wav_path, 'rb') as f:
                    return await f.read()
        finally:
            if temp_mp3_path and os.path.exists(temp_mp3_path): os.remove(temp_mp3_path)
            if temp_wav_path and os.path.exists(temp_wav_path): os.remove(temp_wav_path)
