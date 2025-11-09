import asyncio
from io import BytesIO
import tempfile
import os
import aiofiles
import httpx

from elevenlabs import Voice, VoiceSettings
from elevenlabs.client import AsyncElevenLabs
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from api.core.config import settings
from api.src.user.user_model import User, UserVoice

class TextToSpeechService:
    """ElevenLabs API를 사용하여 텍스트를 음성으로 변환하는 비동기 서비스"""

    def __init__(self, db_session: AsyncSession):
        if not settings.ELEVENLABS_API_KEY:
            raise ValueError("ELEVENLABS_API_KEY가 설정되지 않았습니다.")
        self.client = AsyncElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
        self.db = db_session

    async def _get_or_create_voice_id(
        self,
        user: User,
        audio_sample_bytes: bytes,
        audio_duration_ms: int
    ) -> str:
        """사용자의 voice_id를 조회, 생성 또는 갱신합니다."""
        
        # 1. 기존 voice_id 조회
        stmt = select(UserVoice).where(UserVoice.user_id == user.id)
        result = await self.db.execute(stmt)
        user_voice = result.scalar_one_or_none()

        # 2. voice_id가 이미 존재할 경우
        if user_voice:
            # 목소리가 이미 존재하면, 항상 기존 voice_id를 반환합니다.
            print(f"[VOICE_CACHE] 기존 voice_id 사용: {user_voice.voice_id}")
            return user_voice.voice_id

        # 3. voice_id가 없을 경우 (최초 생성)
        else:
            print(f"[VOICE_CACHE] 최초 voice_id 생성 시작 (user_id: {user.id})")
            
            # [수정] client.voices.ivc.create() 메서드 사용
            new_voice_obj: Voice = await self.client.voices.ivc.create(name=f"user_{user.id}_voice", files=[audio_sample_bytes])
            if not new_voice_obj.voice_id:
                raise ValueError("ElevenLabs에서 voice_id 생성에 실패했습니다.")

            new_user_voice = UserVoice(
                user_id=user.id,
                voice_id=new_voice_obj.voice_id,
                update_count=0,
                source_audio_duration_ms=audio_duration_ms
            )
            self.db.add(new_user_voice)
            await self.db.flush()
            print(f"[VOICE_CACHE] 최초 voice_id 생성 및 저장 완료: {new_user_voice.voice_id}")
            return new_user_voice.voice_id

    async def generate_guide_audio(
        self,
        *,
        user: User,
        text: str,
        audio_sample_bytes: bytes,
        audio_duration_ms: int,
    ) -> bytes:
        """
        사용자의 저장된/생성된 voice_id를 사용하여 가이드 음성을 생성합니다.
        """
        try:
            # --- 1단계: voice_id 가져오기 (Get or Create/Update) ---
            voice_id = await self._get_or_create_voice_id(
                user=user,
                audio_sample_bytes=audio_sample_bytes,
                audio_duration_ms=audio_duration_ms
            )

            # --- 2단계: 생성된 voice_id로 TTS 실행 ---
            print(f"[GUIDE] TTS 음성 스트림 생성 시도 (voice_id: {voice_id})")

            custom_voice_settings = VoiceSettings(
                speed=0.7,
                stability=0.75,         # 안정성을 높여 뒷말 울림 현상 완화
                similarity_boost=0.75,  # 원본 음성과의 유사도
                style=0.0,              # 스타일 과장을 비활성화하여 안정성 확보
                use_speaker_boost=True    # 복제된 목소리의 선명도 향상
            )

            audio_stream_generator = self.client.text_to_speech.convert(
                voice_id=voice_id,
                text=text,
                model_id="eleven_multilingual_v2", 
                output_format="mp3_44100_128",
                voice_settings=custom_voice_settings
            )

            mp3_bytes = b"".join([chunk async for chunk in audio_stream_generator])
            return mp3_bytes

        except Exception as e:
            print(f"ElevenLabs API 호출 중 오류 발생: {e}")
            raise
