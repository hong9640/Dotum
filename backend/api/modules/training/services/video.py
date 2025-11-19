import subprocess
import os
import tempfile
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path
from google.cloud import storage
from api.core.config import settings
import aiofiles
from api.modules.training.services.praat import extract_all_features


class VideoProcessor:
    """FFmpeg를 사용한 동영상 처리 서비스"""
    
    def __init__(self):
        pass  # GCS 클라이언트 의존성 제거
    
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
    
    async def extract_audio_metadata(self, file_path: str) -> Dict[str, Any]:
        """오디오 메타데이터 추출 (오디오 스트림 전용)"""
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
            
            # 오디오 스트림 정보 추출
            audio_stream = None
            for stream in metadata.get('streams', []):
                if stream.get('codec_type') == 'audio':
                    audio_stream = stream
                    break
            
            if not audio_stream:
                raise Exception("No audio stream found")
            
            # duration이 없는 경우 대비
            duration_ms = 0
            if 'duration' in metadata.get('format', {}):
                duration_ms = int(float(metadata['format']['duration']) * 1000)
            elif 'duration' in audio_stream:
                duration_ms = int(float(audio_stream['duration']) * 1000)
            
            return {
                'duration_ms': duration_ms,
                'codec': audio_stream.get('codec_name'),
                'bitrate': metadata['format'].get('bit_rate'),
                'sample_rate': int(audio_stream.get('sample_rate', 0)),
            }
            
        except Exception as e:
            raise Exception(f"Audio metadata extraction failed: {str(e)}")

    async def extract_audio_metadata_from_bytes(self, file_bytes: bytes) -> Dict[str, Any]:
        """바이트 데이터로부터 직접 오디오 메타데이터 추출 (임시 파일 사용)"""
        with tempfile.NamedTemporaryFile(delete=True, suffix=".wav") as temp_file:
            temp_file_path = temp_file.name
            async with aiofiles.open(temp_file_path, 'wb') as f:
                await f.write(file_bytes)
            return await self.extract_audio_metadata(temp_file_path)

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
    
    # 해당 함수 사용 안함. 만약을 위해 주석처리
    # async def process_uploaded_video(
    #     self,
    #     input_video_path: str
    # ) -> Dict[str, Any]:
    #     """
    #     로컬 동영상 파일 처리 (메타데이터, 썸네일 생성).
    #     음성 추출이 필요 없는 경우 사용합니다.
    #     """
    #     # 임시 디렉토리 생성
    #     with tempfile.TemporaryDirectory() as temp_dir:
    #         # 메타데이터 추출
    #         metadata = {}
    #         try:
    #             metadata = await self.extract_metadata(input_video_path)
    #         except Exception as e:
    #             print(f"[VideoProcessor] 메타데이터 추출 실패 (무시하고 계속): {str(e)}")

    #         # 썸네일 생성
    #         thumbnail_path = os.path.join(temp_dir, "thumbnail.jpg")
    #         try:
    #             await self.generate_thumbnail(input_video_path, thumbnail_path)
    #         except Exception as e:
    #             print(f"[VideoProcessor] 썸네일 생성 실패 (무시하고 계속): {str(e)}")
    #             thumbnail_path = None

    #         return {'metadata': metadata, 'thumbnail_path': thumbnail_path}

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
        input_video_path: str
    ) -> Dict[str, Any]:
        """로컬 동영상 파일 처리 (메타데이터, 썸네일, 음성 추출)"""
        # 임시 디렉토리 생성
        with tempfile.TemporaryDirectory() as temp_dir:
            # 메타데이터 추출 (선택적 - 실패해도 계속 진행)
            metadata = {}
            try:
                metadata = await self.extract_metadata(input_video_path)
            except Exception as e:
                print(f"[VideoProcessor] 메타데이터 추출 실패 (무시하고 계속): {str(e)}")
            
            # 썸네일 생성 (선택적 - 실패해도 계속 진행)
            # 썸네일은 GCS 업로드 책임이 호출자에게 있으므로 로컬 경로 반환
            thumbnail_path = os.path.join(temp_dir, "thumbnail.jpg")
            try:
                await self.generate_thumbnail(input_video_path, thumbnail_path)
            except Exception as e:
                print(f"[VideoProcessor] 썸네일 생성 실패 (무시하고 계속): {str(e)}")
                thumbnail_path = None # 실패 시 경로를 None으로 설정
            
            # 음성 추출 (필수)
            # 생성된 임시 오디오 파일은 호출자가 삭제해야 하므로 delete=False로 설정
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio_file:
                audio_path = temp_audio_file.name

            await self.extract_stereo_audio(input_video_path, audio_path)
            
            # WAV 파일 생성 확인
            if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
                raise Exception(f"음성 파일 생성에 실패했거나 파일 크기가 0입니다: {audio_path}")
            
            # praat 추출
            praat_results = None
            try:
                async with aiofiles.open(audio_path, 'rb') as f:
                    wav_bytes = await f.read()
                praat_results = await extract_all_features(wav_bytes)
            except Exception as e:
                print(f"[VideoProcessor] Praat 분석 실패 (무시하고 계속): {str(e)}")

            return {
                'metadata': metadata,
                'thumbnail_path': thumbnail_path if thumbnail_path and os.path.exists(thumbnail_path) else None,
                'audio_path': audio_path,
                'praat_features': praat_results
            }

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
