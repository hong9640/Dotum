import asyncio
from io import BytesIO
from elevenlabs import Voice, VoiceSettings
from elevenlabs.client import AsyncElevenLabs
from api.core.config import settings

class TextToSpeechService:
    """ElevenLabs API를 사용하여 텍스트를 음성으로 변환하는 비동기 서비스"""

    def __init__(self):
        if not settings.ELEVENLABS_API_KEY:
            raise ValueError("ELEVENLABS_API_KEY가 설정되지 않았습니다.")
        self.client = AsyncElevenLabs(api_key=settings.ELEVENLABS_API_KEY)

    async def generate_guide_audio(
        self,
        *,
        text: str,
        audio_sample_bytes: bytes,
    ) -> bytes:
        """
        주어진 음성 샘플을 복제하여 텍스트를 읽는 가이드 음성(WAV/PCM)을 생성합니다.
        (v1.0+ 스타일: 2-Step)
        """
        
        temp_voice_id: str | None = None
        
        try:
            # --- 1단계: 음성 샘플로 임시 보이스 생성 ---
            print("[GUIDE] 1. 임시 음성 복제 시작 (ivc.create 사용)...")
            voice_obj: Voice = await self.client.voices.ivc.create(
                name="Temp Cloned User Voice", 
                files=[audio_sample_bytes]
            )
            
            if not voice_obj.voice_id:
                raise ValueError("ElevenLabs에서 voice_id를 받지 못했습니다.")
            
            temp_voice_id = voice_obj.voice_id
            print(f"[GUIDE] 2. 임시 voice_id 획득: {temp_voice_id}")

            # --- 2단계: 생성된 voice_id로 TTS 실행 ---
            print("[GUIDE] 3. TTS 음성 스트림 생성 시도...")

            custom_voice_settings = VoiceSettings(
                speed=0.5,
                stability=0.75,         # 안정성을 높여 뒷말 울림 현상 완화
                similarity_boost=0.75,  # 원본 음성과의 유사도
                style=0.1,              # 발음을 더 또박또박하게 하기 위한 스타일 과장
            )

            # [최종 수정] 'await'를 제거합니다.
            audio_stream_generator = self.client.text_to_speech.convert(
                voice_id=temp_voice_id, 
                text=text,
                model_id="eleven_multilingual_v2", 
                output_format="mp3_44100_128",
                voice_settings=custom_voice_settings
            )

            print("[GUIDE] 4. TTS 음성 스트림 수신 및 조합 중...")
            mp3_bytes = b"".join([chunk async for chunk in audio_stream_generator])
            print("[GUIDE] 5. MP3 바이트 변환 완료.")
            
            return mp3_bytes

        except Exception as e:
            print(f"ElevenLabs API 호출 중 오류 발생: {e}")
            raise
        
        finally:
            # --- 3단계: 임시 보이스 삭제 ---
            if temp_voice_id:
                try:
                    print(f"[GUIDE] 6. 임시 보이스 삭제 시도: {temp_voice_id}")
                    await self.client.voices.delete(voice_id=temp_voice_id)
                    print(f"[GUIDE] 7. 임시 보이스 삭제 완료: {temp_voice_id}")
                except Exception as e:
                    print(f"임시 보이스({temp_voice_id}) 삭제 중 오류 발생: {e}")