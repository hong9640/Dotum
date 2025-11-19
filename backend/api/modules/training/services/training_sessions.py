from fastapi import BackgroundTasks, UploadFile
import httpx
import logging
from sqlalchemy.ext.asyncio import AsyncSession
import time
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import tempfile
import os
import aiofiles

from ..models.training_session import TrainingSession, TrainingType, TrainingSessionStatus
from ..repositories.training_sessions import TrainingSessionRepository
from ..repositories.training_items import TrainingItemRepository
from ..repositories.media import MediaRepository
from ..repositories.praat import PraatRepository
from ..repositories.session_praat import SessionPraatResultRepository
from ..repositories.stt import SttResultsRepository
from ..repositories.ai_model import AIModelRepository
from ..schemas.training_sessions import (
    TrainingSessionCreate,
    TrainingSessionUpdate,
    TrainingSessionResponse,
    TrainingSessionStatusUpdate,
    CalendarResponse,
    DailyTrainingResponse
)
from ..models.media import MediaFile, MediaType
from ..services.gcs import GCSService
from ..services.video import VideoProcessor
from ..services.media import MediaService
from ..services.text_to_speech import TextToSpeechService
from ..services.praat import get_praat_analysis_from_db, extract_all_features
from ..services.praat_session import save_session_praat_result
from ..services.stt import request_stt_transcription
from api.modules.user.models.model import User
from api.core.config import settings

logger = logging.getLogger(__name__)

class TrainingSessionService:
    """통합된 훈련 세션 서비스"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = TrainingSessionRepository(db)
        self.item_repo = TrainingItemRepository(db)
        self.media_repo = MediaRepository(db)
        self.praat_repo = PraatRepository(db)
        self.session_praat_repo = SessionPraatResultRepository(db)
        self.stt_repo = SttResultsRepository(db)
        self.ai_model_repo = AIModelRepository(db)
    
    async def create_training_session(
        self, 
        user_id: int, 
        session_data: TrainingSessionCreate
    ) -> TrainingSession:
        """훈련 세션 생성"""
        # VOCAL 타입: 랜덤 추출 없이 빈 아이템을 item_count만큼 생성
        if session_data.type == TrainingType.VOCAL:
            training_session = await self.repo.create_session(
                user_id=user_id,
                session_name=session_data.session_name,
                type=session_data.type,
                total_items=session_data.item_count,
                training_date=session_data.training_date,
                session_metadata=session_data.session_metadata
            )
            
            # word_id/sentence_id 모두 None으로 아이템 생성
            for i in range(session_data.item_count):
                await self.repo.create_item(
                    session_id=training_session.id,
                    item_index=i,
                    word_id=None,
                    sentence_id=None
                )
            
            await self.db.commit()
            return training_session
        
        # WORD/SENTENCE 타입: 랜덤 아이템 Id 가져오기
        item_ids = await self._get_random_item_ids(session_data.type, session_data.item_count)
        
        if not item_ids:
            raise ValueError(f"해당 타입({session_data.type})의 아이템을 찾을 수 없습니다")
        
        # 훈련 세션 생성
        training_session = await self.repo.create_session(
            user_id=user_id,
            session_name=session_data.session_name,
            type=session_data.type,
            total_items=len(item_ids),
            training_date=session_data.training_date,
            session_metadata=session_data.session_metadata
        )
        
        # 훈련 아이템들 생성
        await self.item_repo.create_batch(
            training_session.id, 
            item_ids,
            session_data.type
        )
        
        await self.db.commit()
        return training_session
    
    async def _get_random_item_ids(self, training_type: TrainingType, count: int) -> List[int]:
        """훈련 타입에 따른 랜덤 아이템 ID들 가져오기"""
        if training_type == TrainingType.WORD:
            from ..repositories.words import WordRepository
            word_repo = WordRepository(self.db)
            words = await word_repo.get_random(count)
            return [word.id for word in words]
        
        elif training_type == TrainingType.SENTENCE:
            from ..repositories.sentences import SentenceRepository
            sentence_repo = SentenceRepository(self.db)
            sentences = await sentence_repo.get_random(count)
            return [sentence.id for sentence in sentences]
        
        else:
            # 다른 타입들은 추후 구현
            return []
    
    async def get_training_session(
        self, 
        session_id: int, 
        user_id: int
    ) -> Optional[TrainingSession]:
        """훈련 세션 조회"""
        return await self.repo.get_session(session_id, user_id)
    
    async def get_user_training_sessions(
        self, 
        user_id: int,
        type: Optional[TrainingType] = None,
        status: Optional[TrainingSessionStatus] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[TrainingSession]:
        """사용자의 훈련 세션 목록 조회"""
        return await self.repo.get_user_sessions(
            user_id=user_id,
            type=type,
            status=status,
            limit=limit,
            offset=offset
        )
    
    async def get_training_sessions_by_date(
        self, 
        user_id: int, 
        training_date: date,
        type: Optional[TrainingType] = None
    ) -> List[TrainingSession]:
        """특정 날짜의 훈련 세션 조회"""
        return await self.repo.get_sessions_by_date(
            user_id=user_id,
            training_date=training_date,
            type=type
        )
    
    async def get_training_calendar(
        self, 
        user_id: int, 
        year: int, 
        month: int,
        type: Optional[TrainingType] = None
    ) -> Dict[str, int]:
        """월별 훈련 달력 조회"""
        return await self.repo.get_calendar_data(
            user_id=user_id,
            year=year,
            month=month,
            type=type
        )
    
    
    async def complete_training_session(
        self, 
        session_id: int, 
        user_id: int
    ) -> Optional[TrainingSession]:
        """훈련 세션 완료"""
        session = await self.get_training_session(session_id, user_id)
        if not session:
            return None
        
        if not session.can_complete():
            raise ValueError("세션을 완료할 수 없습니다. 현재 상태를 확인해주세요.")
        
        # 100% 완료 여부 검증 (결과보기 조건 강화)
        if session.total_items == 0 or session.completed_items != session.total_items:
            raise ValueError("모든 아이템이 완료되지 않았습니다.")
        
        # WORD/SENTENCE 타입인 경우 STT 결과가 모두 완료될 때까지 대기
        if session.type in (TrainingType.WORD, TrainingType.SENTENCE):
            logger.info(f"[Complete] {session.type.value} 세션 완료 - STT 결과 대기 시작: session_id={session_id}")
            await self._wait_for_stt_completion(session_id, session.total_items, max_wait_seconds=60)
        
        # 세션 상태를 완료로 변경
        await self.repo.update_status(
            session_id, 
            TrainingSessionStatus.COMPLETED,
            user_id
        )
        
        # 모든 타입의 세션 Praat 평균 결과 저장 (이미 조회한 세션 객체 전달하여 재조회 방지)
        try:
            await save_session_praat_result(self.db, session_id, session)
        except Exception as e:
            # Praat 평균 계산 실패해도 세션 완료는 정상 처리
            print(f"⚠️ Session {session_id}: Praat 평균 결과 저장 실패: {e}")
            logger.error(f"Session {session_id}: Praat 평균 결과 저장 실패: {e}", exc_info=True)
        
        # 세션 상태 변경 및 session_praat_result 저장을 위해 commit 필요
        await self.db.commit()
        
        return await self.get_training_session(session_id, user_id)
    
    
    async def update_session_status(
        self, 
        session_id: int, 
        user_id: int,
        status_update: TrainingSessionStatusUpdate
    ) -> Optional[TrainingSession]:
        """세션 상태 업데이트 (유연한 상태 전환)"""
        session = await self.get_training_session(session_id, user_id)
        if not session:
            return None
        
        # 상태 전환 검증
        if not self._is_valid_status_transition(session.status, status_update.status):
            raise ValueError(f"상태 전환이 불가능합니다: {session.status} -> {status_update.status}")
        
        await self.repo.update_status(
            session_id, 
            status_update.status,
            user_id
        )
        await self.db.commit()
        
        return await self.get_training_session(session_id, user_id)

    
    async def complete_training_item(
        self, 
        session_id: int, 
        item_id: int, 
        video_url: str, 
        media_file_id: Optional[int],
        is_completed: bool,
        user_id: int
    ) -> Optional[TrainingSession]:
        """훈련 아이템 완료 처리 (자동 진행률 업데이트)"""
        # 아이템 완료 처리
        await self.item_repo.complete_item(item_id, video_url, media_file_id, is_completed)
        
        # 세션 진행률 자동 업데이트
        completed_count = await self.repo.get_completed_items_count(session_id)
        await self.repo.update_progress(session_id, completed_count)
        
        # 다음 아이템으로 이동
        await self.repo.move_to_next_item(session_id)
        
        await self.db.commit()
        
        return await self.get_training_session(session_id, user_id)
    
    async def _wait_for_stt_completion(
        self,
        session_id: int,
        expected_count: int,
        max_wait_seconds: int = 60,
        check_interval: float = 1.0
    ):
        """
        세션의 모든 STT 결과가 완료될 때까지 대기
        
        Args:
            session_id: 세션 ID
            expected_count: 예상 STT 결과 개수 (total_items)
            max_wait_seconds: 최대 대기 시간 (초)
            check_interval: 확인 간격 (초)
        """
        start_time = time.time()
        elapsed = 0
        
        while elapsed < max_wait_seconds:
            # STT 결과 조회
            stt_results = await self.stt_repo.get_by_session_id(session_id)
            current_count = len(stt_results)
            
            logger.info(f"[STT Wait] session_id={session_id}, STT 완료: {current_count}/{expected_count}, 경과 시간: {elapsed:.1f}초")
            
            if current_count >= expected_count:
                logger.info(f"[STT Wait] ✅ 모든 STT 처리 완료 - session_id={session_id}, 총 대기 시간: {elapsed:.1f}초")
                return
            
            # 대기
            await asyncio.sleep(check_interval)
            elapsed = time.time() - start_time
        
        # 타임아웃
        stt_results = await self.stt_repo.get_by_session_id(session_id)
        current_count = len(stt_results)
        logger.warning(
            f"[STT Wait] ⚠️ STT 대기 타임아웃 - session_id={session_id}, "
            f"완료: {current_count}/{expected_count}, 대기 시간: {elapsed:.1f}초"
        )
        # 타임아웃이어도 예외를 발생시키지 않고 계속 진행 (LLM 피드백은 가능한 결과만 사용)
    
    @staticmethod
    async def _process_stt_with_independent_session(audio_gs_path: str, item_id: int):
        """
        독립적인 DB 세션에서 STT 처리를 수행하는 정적 메서드
        BackgroundTasks에서 호출되므로 독립 세션 필요
        """
        from api.core.database import async_session
        
        async with async_session() as db:
            try:
                start_time = time.time()
                logger.info(f"[Background STT] 시작 - item_id: {item_id}, audio_gs_path: {audio_gs_path}")
                
                # Repository 초기화
                from ..repositories.stt import SttResultsRepository
                from ..repositories.ai_model import AIModelRepository
                stt_repo = SttResultsRepository(db)
                ai_model_repo = AIModelRepository(db)
                
                # STT 요청 (재시도 로직 포함 - 모델 초기화 시간 고려)
                stt_response = None
                max_retries = 3
                retry_delays = [5.0, 30.0, 60.0]  # 첫 번째: 5초, 두 번째: 30초, 세 번째: 60초
                
                for attempt in range(max_retries):
                    stt_response = await request_stt_transcription(audio_gs_path, timeout=300.0)  # 5분으로 증가
                    
                    if stt_response and stt_response.get("success"):
                        break
                    
                    if attempt < max_retries - 1:
                        delay = retry_delays[attempt]
                        logger.warning(f"[Background STT] 재시도 {attempt + 1}/{max_retries} ({delay}초 후) - item_id: {item_id}")
                        await asyncio.sleep(delay)
                
                if stt_response and stt_response.get("success"):
                    transcription = stt_response.get("transcription", "")
                    process_time_ms = stt_response.get("process_time_ms", 0)
                    
                    logger.info(f"[Background STT] STT 요청 성공 - item_id: {item_id}, transcription: {transcription}, process_time: {process_time_ms}ms")
                    
                    # AI 모델 조회 또는 생성
                    model_version = stt_response.get("model_version", "whisper-large-v3")
                    ai_model = await ai_model_repo.get_or_create(model_version)
                    
                    # STT 결과 저장
                    stt_result = await stt_repo.create_and_flush(
                        training_item_id=item_id,
                        ai_model_id=ai_model.id,
                        stt_result=transcription
                    )
                    
                    await db.commit()
                    
                    elapsed_time = time.time() - start_time
                    logger.info(f"[Background STT] ✅ 완료 - item_id: {item_id}, stt_id: {stt_result.id}, elapsed: {elapsed_time:.2f}초")
                    
                else:
                    logger.warning(f"[Background STT] ❌ STT 요청 실패 - item_id: {item_id}")
                    
            except Exception as e:
                logger.error(f"[Background STT] ❌ 예외 발생 - item_id: {item_id}, error: {e}", exc_info=True)
                await db.rollback()
    
    async def trigger_wav2lip_processing(
        self,
        guide_audio_gs_path: str,  # ElevenLabs로 생성된 가이드 음성 경로
        user_video_gs_path: str,
        output_video_gs_path: str,
        user_id: int,
        output_object_key: str
    ):
        """외부 wav2lip 서버에 처리를 요청하는 백그라운드 작업"""
        start_time = time.time()
        WAV2LIP_API_URL = f"{settings.ML_SERVER_URL}/api/v1/lip-video"
        
        payload = {
            "gen_audio_gs": f"gs://{guide_audio_gs_path}",  # ElevenLabs 생성 오디오
            "user_video_gs": f"gs://{user_video_gs_path}",
            "output_video_gs": f"gs://{output_video_gs_path}"
        }

        try:
            # 외부 API 호출 (httpx 라이브러리 필요)
            print(f"[WAV2LIP] ML 서버로 Wav2Lip 요청 전송 중... URL: {WAV2LIP_API_URL}")
            print(f"[WAV2LIP] Payload: {payload}")
            
            # Wav2Lip 처리 시간은 예측 어려움 → 타임아웃 제거
            async with httpx.AsyncClient(timeout=None) as client:
                response = await client.post(WAV2LIP_API_URL, json=payload)
                response.raise_for_status()
                logger.info(f"Wav2Lip 작업 요청 성공: {response.json()}")

                gcs_service = GCSService(settings)

                # 2. GCS에서 결과 파일의 메타데이터(정보) 가져오기
                blob = gcs_service.bucket.get_blob(output_object_key)
                file_size = 0
                if blob:
                    file_size = blob.size # 파일 크기(bytes)
                    print(f"[WAV2LIP] GCS 결과 파일 크기: {file_size} bytes")
                else:
                    logger.warning(f"GCS에서 {output_object_key} 파일을 찾을 수 없어 파일 크기를 0으로 저장합니다.")

                # 3. MediaFile 객체 생성 시 file_size_bytes에 값 할당
                result_media_file = await self.media_repo.create_and_flush(
                    user_id=user_id,
                    object_key=output_object_key,
                    media_type=MediaType.TRAIN,
                    file_name=output_object_key.split('/')[-1],
                    format="mp4",
                    file_size_bytes=file_size,
                )
                await self.db.commit()
                logger.info(f"Wav2Lip 결과 미디어 파일 정보 저장 성공: {result_media_file.id}")
        
        except httpx.RequestError as e:
            elapsed_time = time.time() - start_time
            logger.error(f"Wav2Lip 작업 요청 실패: {e} (소요 시간: {elapsed_time:.2f}초)", exc_info=True)
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"Wav2Lip 결과 저장 중 DB 오류 발생: {e} (소요 시간: {elapsed_time:.2f}초)", exc_info=True)
        finally:
            elapsed_time = time.time() - start_time
            logger.info(f"Wav2Lip 처리 작업 완료. (총 소요 시간: {elapsed_time:.2f}초)")
    
    async def trigger_guide_audio_generation(
        self,
        *,
        user: User,
        session_id: int,
        item_id: int,
        text: str,
        original_audio_object_key: str,
        gcs_service: GCSService,
        original_video_object_key: str # Wav2Lip 처리를 위해 원본 비디오 경로 추가
    ):
        """백그라운드 작업: 원본 음성을 복제하여 가이드 음성을 생성하고 GCS에 저장"""
        start_time = time.time()
        try:
            logger.info(f"가이드 음성 생성 시작 - item_id: {item_id}, user: {user.username}")
            
            # 1. GCS에서 원본 음성 파일 다운로드
            guide_audio_object_key = f"guides/{user.username}/{session_id}/guide_item_{item_id}.wav"

            # [수정] 기존 가이드 음성 MediaFile 레코드가 있으면 삭제
            media_service = MediaService(self.db)
            existing_guide_media = await media_service.get_media_file_by_object_key(guide_audio_object_key)
            if existing_guide_media:
                logger.info(f"기존 가이드 음성 DB 레코드가 존재합니다. 덮어쓰기를 진행합니다. (media_id: {existing_guide_media.id})")

            original_audio_bytes = await gcs_service.download_video(original_audio_object_key)
            if not original_audio_bytes:
                logger.error(f"가이드 음성 생성을 위한 원본 음성 다운로드 실패: {original_audio_object_key}")
                return

            # 2. ElevenLabs TTS로 MP3 음성 생성 (음성 복제)
            print(f"[ELEVENLABS] ElevenLabs API 호출 중...")
            video_processor = VideoProcessor()
            tts_service = TextToSpeechService(db_session=self.db)
            
            # 원본 오디오의 길이를 밀리초 단위로 추출
            audio_duration_ms = 0
            try:
                # 새로 추가한 오디오 전용 함수를 사용합니다.
                metadata = await video_processor.extract_audio_metadata_from_bytes(original_audio_bytes)
                audio_duration_ms = metadata.get('duration_ms', 0)
                logger.info(f"가이드 음성 생성을 위한 원본 오디오 길이: {audio_duration_ms}ms")
            except Exception as e:
                logger.error(f"오디오 길이 추출 실패 (기본값 0 사용): {e}")

            mp3_bytes = await tts_service.generate_guide_audio(
                user=user,
                text=text, audio_sample_bytes=original_audio_bytes,
                audio_duration_ms=audio_duration_ms
            )
            if not mp3_bytes:
                print(f"[ELEVENLABS] ElevenLabs 가이드 음성(MP3) 생성 실패 - item_id: {item_id}")
                return
            print(f"[ELEVENLABS] ElevenLabs 가이드 음성(MP3) 생성 성공 - 크기: {len(mp3_bytes)} bytes")

            # 3. MP3를 WAV로 변환
            video_processor = VideoProcessor()
            wav_bytes = await video_processor.convert_mp3_to_wav(mp3_bytes)
            if not wav_bytes:
                logger.error(f"가이드 음성(WAV) 변환 실패 - item_id: {item_id}")
                return
            print(f"[ELEVENLABS] WAV 변환 완료 - 크기: {len(wav_bytes)} bytes")

            # 4. GCS에 '가이드 음성'을 다른 이름으로 업로드
            guide_audio_blob = gcs_service.bucket.blob(guide_audio_object_key)
            guide_audio_blob.upload_from_string(wav_bytes, content_type="audio/wav")
            logger.info(f"가이드 음성 GCS 업로드 성공: {guide_audio_object_key}")

            # 5. MediaFile DB에 '가이드 음성' 정보 저장 또는 업데이트
            if existing_guide_media:
                # 기존 레코드가 있으면 업데이트 (덮어쓰기)
                await self.media_repo.update_media_file(
                    media_file=existing_guide_media,
                    file_size_bytes=len(wav_bytes)
                )
            else:
                # 기존 레코드가 없으면 새로 생성
                await self.media_repo.create_and_flush(
                    user_id=user.id,
                    object_key=guide_audio_object_key,
                    media_type=MediaType.AUDIO,
                    file_name=guide_audio_object_key.split('/')[-1],
                    file_size_bytes=len(wav_bytes),
                    format="wav"
                )
            await self.db.commit() # DB에 최종 반영
            logger.info(f"가이드 음성 DB 저장 성공 - item_id: {item_id}")

            # [이동된 로직] Wav2Lip 처리 요청
            # ElevenLabs로 생성된 가이드 음성을 사용하여 Wav2Lip 처리를 트리거합니다.
            # 환경변수로 wav2lip 처리 활성화 여부를 제어합니다.
            if settings.ENABLE_WAV2LIP:
                output_object_key = f"results/{user.username}/{session_id}/result_item_{item_id}.mp4"
                user_video_full_path = f"{gcs_service.bucket_name}/{original_video_object_key}"
                output_video_full_path = f"{gcs_service.bucket_name}/{output_object_key}"
                guide_audio_full_path = f"{gcs_service.bucket_name}/{guide_audio_object_key}"

                print(f"[WAV2LIP] ElevenLabs 가이드 음성으로 Wav2Lip 처리 요청 - item_id: {item_id}")
                print(f"[WAV2LIP] 가이드 음성: {guide_audio_full_path}")
                print(f"[WAV2LIP] 사용자 비디오: {user_video_full_path}")
                await self.trigger_wav2lip_processing(
                    guide_audio_gs_path=guide_audio_full_path,  # ElevenLabs 생성 가이드 음성
                    user_video_gs_path=user_video_full_path,
                    output_video_gs_path=output_video_full_path,
                    user_id=user.id,
                    output_object_key=output_object_key
                )
            else:
                logger.info(f"[WAV2LIP] Wav2Lip 처리가 비활성화되어 있습니다 (ENABLE_WAV2LIP=False) - item_id: {item_id}")

        except Exception as e:
            await self.db.rollback()
            elapsed_time = time.time() - start_time
            logger.error(f"가이드 음성 생성/저장 중 오류 발생 - item_id: {item_id}: {e} (소요 시간: {elapsed_time:.2f}초)", exc_info=True)
        finally:
            elapsed_time = time.time() - start_time
            logger.info(f"가이드 음성 생성 작업 완료 - item_id: {item_id}. (총 소요 시간: {elapsed_time:.2f}초)")

    async def _submit_item_with_video(
        self,
        *,
        session: TrainingSession,
        item_id: int,
        user: User,
        video_file: UploadFile,
        filename: str,
        content_type: str,
        gcs_service: GCSService,
        background_tasks: BackgroundTasks
    ) -> Dict[str, Any]:
        """내부 메서드: 특정 아이템에 동영상 업로드 및 완료 처리"""
        start_time = time.time()
        temp_video_path = None
        processing_result = None
        audio_path = None

        logger.info(f"[_submit_item_with_video] 시작 - session_id: {session.id}, item_id: {item_id}")
        
        item = await self.item_repo.get_item(session.id, item_id, include_relations=True)
        if not item:
            raise LookupError("훈련 아이템을 찾을 수 없습니다.")
        
        if item.is_completed:
            raise ValueError("이미 완료된 아이템입니다.")
        
        try:
            # 1. UploadFile을 임시 파일로 저장
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
                temp_video_path = temp_video.name
                # 비동기적으로 파일 쓰기
                async with aiofiles.open(temp_video_path, 'wb') as out_file:
                    while content := await video_file.read(1024 * 1024):  # 1MB씩 읽기
                        await out_file.write(content)
            
            # 2. GCS에 동영상 업로드 (로컬 경로 사용)
            upload_result = await gcs_service.upload_video(
                file_path=temp_video_path,
                username=user.username,
                session_id=str(session.id),
                train_id=item.id,
                word_id=item.word_id,
                sentence_id=item.sentence_id,
                original_filename=filename,
                content_type=content_type
            )
            if not upload_result.get("success"):
                raise RuntimeError(f"동영상 업로드에 실패했습니다: {upload_result.get('error')}")
            
            object_key = upload_result.get("object_path")
            video_url = await gcs_service.get_signed_url(object_key, expiration_hours=24)
            if not video_url:
                raise RuntimeError("동영상 URL 생성에 실패했습니다.")

            # 3. 로컬 임시 파일을 사용하여 미디어 처리
            video_processor = VideoProcessor()
            logger.info(f"[_submit_item_with_video] 로컬 파일로 음성 처리 시작 - path: {temp_video_path}")
            processing_result = await video_processor.process_uploaded_video_with_audio(temp_video_path)
            logger.info(f"[_submit_item_with_video] 로컬 파일 음성 처리 완료")

            # 4. 동영상 파일 정보 DB 저장
            media_file = await self.media_repo.create_and_flush(
                user_id=user.id,
                object_key=object_key,
                media_type=MediaType.VIDEO,
                file_name=upload_result.get("filename") or filename,
                file_size_bytes=upload_result.get("file_size", 0),
                format=(content_type.split('/')[-1] if '/' in content_type else content_type)
            )
            logger.info(f"[_submit_item_with_video] 동영상 정보 DB 저장 완료 (media_id: {media_file.id})")

            # 5. 추출된 음성 파일 처리
            audio_media_file = None
            new_praat_record = None
            audio_path = processing_result.get('audio_path')

            if audio_path and os.path.exists(audio_path):
                # 5-1. 음성 파일을 GCS에 업로드
                audio_object_key = object_key.replace('.mp4', '.wav')
                audio_blob = gcs_service.bucket.blob(audio_object_key)
                audio_blob.upload_from_filename(audio_path, content_type="audio/wav")
                logger.info(f"[_submit_item_with_video] 추출된 음성 파일 GCS 업로드 완료: {audio_object_key}")

                # 5-2. 음성 파일 정보 DB 저장
                audio_media_file = await self.media_repo.create_and_flush(
                    user_id=user.id,
                    object_key=audio_object_key,
                    media_type=MediaType.AUDIO,
                    file_name=audio_object_key.split('/')[-1],
                    file_size_bytes=os.path.getsize(audio_path),
                    format="wav"
                )
                logger.info(f"[_submit_item_with_video] 음성 정보 DB 저장 완료 - media_id: {audio_media_file.id}")

                # 5-3. Praat 분석 결과 DB 저장
                praat_data = processing_result.get('praat_features')
                if praat_data:
                    new_praat_record = await self.praat_repo.create_and_flush(
                        media_id=audio_media_file.id,
                        **praat_data
                    )
                    logger.info(f"[_submit_item_with_video] Praat DB 저장 완료 - praat_id: {new_praat_record.id}")
            else:
                logger.warning(f"[_submit_item_with_video] 경고: 음성 파일이 생성되지 않았습니다.")

            # 6. STT 백그라운드 처리 추가 (WORD/SENTENCE 타입) - 병렬 처리!
            if audio_media_file and session.type in (TrainingType.WORD, TrainingType.SENTENCE):
                audio_gs_path = f"gs://{settings.GCS_BUCKET_NAME}/{audio_media_file.object_key}"
                logger.info(f"[_submit_item_with_video] STT 백그라운드 처리 예약 (병렬) - item_id: {item.id}, audio_gs_path: {audio_gs_path}")
                
                # asyncio.create_task로 병렬 처리 (BackgroundTasks 순차 실행 문제 회피)
                asyncio.create_task(
                    self._process_stt_with_independent_session(audio_gs_path, item.id)
                )

            # 6-1. 가이드 음성 생성 백그라운드 작업 추가 (STT 이후 처리)
            if (item.word or item.sentence) and audio_media_file:
                logger.info(f"[_submit_item_with_video] 가이드 음성 생성 백그라운드 작업 추가 (우선순위 2) - item_id: {item.id}")
                text_for_guide = item.word.word if item.word else item.sentence.sentence
                background_tasks.add_task(
                    self.trigger_guide_audio_generation,
                    user=user,
                    session_id=session.id,
                    item_id=item.id,
                    text=text_for_guide,
                    original_audio_object_key=audio_media_file.object_key,
                    gcs_service=gcs_service,
                    original_video_object_key=object_key
                )

            # 7. 아이템 완료 처리
            await self.item_repo.complete_item(
                item_id=item.id, video_url=video_url, media_file_id=media_file.id, is_completed=True
            )
            
            completed_count = await self.repo.get_completed_items_count(session.id)
            await self.repo.update_progress(session.id, completed_count)
            await self.repo.move_to_next_item(session.id)
            
            await self.db.commit()
            await self.db.refresh(media_file)
            if audio_media_file:
                await self.db.refresh(audio_media_file)
            
            updated_session = await self.get_training_session(session.id, user.id)
            next_item = await self.item_repo.get_current_item(session.id, include_relations=True)
            has_next = await self.item_repo.get_next_item(session.id, next_item.item_index) is not None if next_item else False
            
            return {
                "session": updated_session, "next_item": next_item, "media_file": media_file,
                "praat_feature": new_praat_record, "audio_media_file": audio_media_file,
                "video_url": video_url, "has_next": has_next
            }
        finally:
            # 8. 임시 파일 정리
            if temp_video_path and os.path.exists(temp_video_path):
                os.remove(temp_video_path)
                logger.info(f"임시 동영상 파일 삭제: {temp_video_path}")
            if audio_path and os.path.exists(audio_path):
                os.remove(audio_path)
                logger.info(f"임시 음성 파일 삭제: {audio_path}")
            
            elapsed_time = time.time() - start_time
            logger.info(f"[_submit_item_with_video] 완료 - session_id: {session.id}, item_id: {item.id}. (총 소요 시간: {elapsed_time:.2f}초)")
    
    async def submit_current_item_with_video(
        self,
        *,
        session_id: int,
        user: User,
        video_file: UploadFile,
        filename: str,
        content_type: str,
        gcs_service: GCSService,
        background_tasks: BackgroundTasks
    ) -> Dict[str, Any]:
        """현재 진행 중인 아이템에 동영상 업로드 및 완료 처리"""
        start_time = time.time()
        session = await self.get_training_session(session_id, user.id)
        if not session:
            raise LookupError("훈련 세션을 찾을 수 없습니다.")
        
        # 현재 진행 중인 아이템 조회
        current_item = await self.item_repo.get_current_item(session_id, include_relations=True)
        if not current_item:
            raise LookupError("진행 중인 아이템을 찾을 수 없습니다.")
        
        if current_item.is_completed:
            raise ValueError("이미 완료된 아이템입니다.")
        
        # 내부 메서드 호출
        # 로깅 사용을 위해 return을 맨 마지막에 명시
        result = await self._submit_item_with_video(
            session=session,
            item_id=current_item.id,
            user=user,
            video_file=video_file,
            filename=filename,
            content_type=content_type,
            gcs_service=gcs_service,
            background_tasks=background_tasks
        )
        elapsed_time = time.time() - start_time
        logger.info(f"[submit_current_item_with_video] 완료 - session_id: {session_id}. (총 소요 시간: {elapsed_time:.2f}초)")
        return result
    
    async def resubmit_item_video(
        self,
        *,
        session_id: int,
        item_id: int,
        user: User,
        video_file: UploadFile,
        filename: str,
        content_type: str,
        gcs_service: GCSService,
        background_tasks: BackgroundTasks
    ) -> Dict[str, Any]:
        """특정 아이템의 동영상을 재업로드(덮어쓰기).
        완료된 아이템도 허용하며 진행률/포인터는 변경하지 않는다.
        같은 경로에 새 파일을 업로드하여 기존 파일을 덮어쓴다.
        """
        start_time = time.time()
        temp_video_path = None
        processing_result = None
        audio_path = None
        logger.info(f"[resubmit_item_video] 시작 - session_id: {session_id}, item_id: {item_id}")

        session = await self.get_training_session(session_id, user.id)
        if not session:
            raise LookupError("훈련 세션을 찾을 수 없습니다.")

        item = await self.item_repo.get_item(session_id, item_id, include_relations=True)
        if not item:
            raise LookupError("훈련 아이템을 찾을 수 없습니다.")

        # 기존 미디어 파일 정보 가져오기 (덮어쓰기용)
        old_media_file = None
        if item.media_file_id:
            old_media_file = item.media_file # Eager Loading으로 이미 로드된 객체 사용

        try:
            # 1. UploadFile을 임시 파일로 저장
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
                temp_video_path = temp_video.name
                async with aiofiles.open(temp_video_path, 'wb') as out_file:
                    while content := await video_file.read(1024 * 1024):
                        await out_file.write(content)

            # 2. GCS에 동영상 업로드 (덮어쓰기)
            upload_result = await gcs_service.upload_video(
                file_path=temp_video_path,
                username=user.username,
                session_id=str(session_id),
                train_id=item.id,
                word_id=item.word_id,
                sentence_id=item.sentence_id,
                original_filename=filename,
                content_type=content_type
            )
            if not upload_result.get("success"):
                raise RuntimeError(f"동영상 재업로드에 실패했습니다: {upload_result.get('error')}")

            object_key = upload_result.get("object_path")
            video_url = await gcs_service.get_signed_url(object_key, expiration_hours=24)
            if not video_url:
                raise RuntimeError("동영상 URL 생성에 실패했습니다.")

            # 3. 기존 미디어 파일이 있으면 업데이트, 없으면 새로 생성
            if old_media_file:
                media_file = await self.media_repo.update_media_file(
                    media_file=old_media_file,
                    file_name=upload_result.get("filename") or filename,
                    file_size_bytes=upload_result.get("file_size", 0),
                    format=content_type.split('/')[-1] if '/' in content_type else content_type
                )
            else:
                media_file = await self.media_repo.create_and_flush(
                    user_id=user.id, object_key=object_key, media_type=MediaType.VIDEO,
                    file_name=upload_result.get("filename") or filename,
                    file_size_bytes=upload_result.get("file_size", 0),
                    format=(content_type.split('/')[-1] if '/' in content_type else content_type)
                )

            # 4. 로컬 임시 파일을 사용하여 미디어 처리
            video_processor = VideoProcessor()
            logger.info(f"[resubmit_item_video] 로컬 파일로 음성 처리 시작 - path: {temp_video_path}")
            processing_result = await video_processor.process_uploaded_video_with_audio(temp_video_path)
            logger.info(f"[resubmit_item_video] 로컬 파일 음성 처리 완료")

            # 5. 추출된 음성 파일 처리
            audio_media_file = None
            new_praat_record = None
            audio_path = processing_result.get('audio_path')

            if audio_path and os.path.exists(audio_path):
                # 5-1. 음성 파일을 GCS에 업로드
                audio_object_key = object_key.replace('.mp4', '.wav')
                audio_blob = gcs_service.bucket.blob(audio_object_key)
                audio_blob.upload_from_filename(audio_path, content_type="audio/wav")
                logger.info(f"[resubmit_item_video] 추출된 음성 파일 GCS 업로드 완료: {audio_object_key}")

                # 5-2. 음성 파일 정보 DB 업데이트 또는 생성
                media_service = MediaService(self.db)
                existing_audio = await media_service.get_media_file_by_object_key(audio_object_key)
                if existing_audio:
                    logger.info(f"[resubmit_item_video] 기존 오디오 DB 레코드 업데이트 - media_id: {existing_audio.id}")
                    audio_media_file = await self.media_repo.update_media_file(
                        media_file=existing_audio,
                        file_name=audio_object_key.split('/')[-1],
                        file_size_bytes=os.path.getsize(audio_path),
                        format="wav"
                    )
                else:
                    logger.info(f"[resubmit_item_video] 새 오디오 DB 레코드 생성")
                    audio_media_file = await self.media_repo.create_and_flush(
                        user_id=user.id, object_key=audio_object_key, media_type=MediaType.AUDIO,
                        file_name=audio_object_key.split('/')[-1],
                        file_size_bytes=os.path.getsize(audio_path), format="wav"
                    )

                # 5-3. Praat 분석 결과 DB 업데이트 또는 생성
                praat_data = processing_result.get('praat_features')
                if praat_data and audio_media_file:
                    existing_praat = await self.praat_repo.get_by_media_id(audio_media_file.id)
                    if existing_praat:
                        logger.info(f"[resubmit_item_video] Praat DB 업데이트 - praat_id: {existing_praat.id}")
                        for key, value in praat_data.items():
                            setattr(existing_praat, key, value)
                        new_praat_record = await self.praat_repo.update(existing_praat)
                    else:
                        logger.info(f"[resubmit_item_video] Praat DB 생성 - media_id: {audio_media_file.id}")
                        new_praat_record = await self.praat_repo.create_and_flush(
                            media_id=audio_media_file.id, **praat_data
                        )
            else:
                logger.warning(f"[resubmit_item_video] 경고: 음성 파일이 생성되지 않았습니다.")

            # 6. 가이드 음성 생성 백그라운드 작업 추가
            if (item.word or item.sentence) and audio_media_file:
                logger.info(f"[resubmit_item_video] 가이드 음성 생성 백그라운드 작업 추가 - item_id: {item.id}")
                text_for_guide = item.word.word if item.word else item.sentence.sentence
                background_tasks.add_task(
                    self.trigger_guide_audio_generation,
                    user=user, session_id=session_id, item_id=item.id, text=text_for_guide,
                    original_audio_object_key=audio_media_file.object_key,
                    gcs_service=gcs_service, original_video_object_key=object_key
                )

            # 7. 아이템의 동영상 정보 업데이트 (완료 상태 유지)
            await self.item_repo.complete_item(
                item_id=item.id, video_url=video_url, media_file_id=media_file.id, is_completed=True
            )

            await self.db.commit()
            await self.db.refresh(media_file)
            if audio_media_file:
                await self.db.refresh(audio_media_file)
            if new_praat_record:
                await self.db.refresh(new_praat_record)

            updated_session = await self.get_training_session(session_id, user.id)

            return {
                "session": updated_session, "next_item": None, "media_file": media_file,
                "praat_feature": new_praat_record, "audio_media_file": audio_media_file,
                "video_url": video_url, "has_next": False
            }
        finally:
            # 8. 임시 파일 정리
            if temp_video_path and os.path.exists(temp_video_path):
                os.remove(temp_video_path)
                logger.info(f"임시 동영상 파일 삭제: {temp_video_path}")
            if audio_path and os.path.exists(audio_path):
                os.remove(audio_path)
                logger.info(f"임시 음성 파일 삭제: {audio_path}")
            
            elapsed_time = time.time() - start_time
            logger.info(f"[resubmit_item_video] 완료 - session_id: {session_id}, item_id: {item_id}. (총 소요 시간: {elapsed_time:.2f}초)")
    
    async def get_wav2lip_result(
        self,
        *,
        session_id: int,
        item_id: int,
        user: User,
        gcs_service: GCSService
    ) -> Optional[Dict[str, Any]]:
        """Wav2Lip 결과 영상의 서명된 URL을 조회합니다."""
        # 1. 세션 및 아이템 존재 여부와 소유권 확인
        item = await self.item_repo.get_item(session_id, item_id, include_relations=False)
        if not item:
            raise LookupError("훈련 아이템을 찾을 수 없습니다.")
        session = await self.repo.get_session_by_id(item.training_session_id)
        if not session or session.user_id != user.id:
            raise LookupError("훈련 아이템을 찾을 수 없거나 접근 권한이 없습니다.")

        # 2. 예상되는 object_key 생성
        object_key = f"results/{user.username}/{session_id}/result_item_{item_id}.mp4"

        # 3. DB에서 해당 object_key를 가진 미디어 파일 조회
        media_service = MediaService(self.db)
        media_file = await media_service.get_media_file_by_object_key(object_key)

        # 4. 파일이 DB에 없거나, 타입이 TRAIN이 아니면 처리 중으로 간주
        if not media_file or media_file.media_type != MediaType.TRAIN:
            return None

        # 5. 서명된 URL 생성 및 반환
        signed_url = await gcs_service.get_signed_url(media_file.object_key, expiration_hours=1)
        if not signed_url:
            raise RuntimeError("결과 영상의 URL 생성에 실패했습니다.")
        
        return {
            "media_file": media_file,
            "signed_url": signed_url
        }

    async def get_current_item(
        self,
        session_id: int,
        user_id: int
    ):
        """현재 세션의 진행 중인 아이템 조회"""
        # 세션 소유권 확인
        session = await self.get_training_session(session_id, user_id)
        if not session:
            return None
        
        # 현재 아이템 조회
        current_item = await self.item_repo.get_current_item(session_id, include_relations=True)
        
        if not current_item:
            return None
        
        # 다음 아이템 존재 여부 확인
        has_next = await self.item_repo.get_next_item(session_id, current_item.item_index) is not None

        # Praat 분석 결과 조회 (이미 DB에 저장된 값 사용)
        praat_feature = None
        try:
            if current_item.media_file_id:
                media_file = await self.get_media_file_by_id(current_item.media_file_id)
                if media_file:
                    # VOCAL 타입: media_file_id가 이미 오디오를 가리킴
                    # WORD/SENTENCE 타입: media_file_id는 비디오를 가리키므로 .mp4 -> .wav 치환 필요
                    if session.type == TrainingType.VOCAL:
                        # VOCAL: media_file_id가 이미 오디오 media_id
                        if media_file.user_id == user_id:
                            praat_feature = await self.praat_repo.get_by_media_id(media_file.id)
                    else:
                        # WORD/SENTENCE: video media에서 audio media 찾기
                        if media_file.object_key and media_file.object_key.endswith('.mp4'):
                            audio_object_key = media_file.object_key.replace('.mp4', '.wav')
                            from ..services.media import MediaService
                            media_service = MediaService(self.db)
                            audio_media = await media_service.get_media_file_by_object_key(audio_object_key)
                            if audio_media and audio_media.user_id == user_id:
                                praat_feature = await self.praat_repo.get_by_media_id(audio_media.id)
        except Exception:
            pass
        
        return {
            'item': current_item,
            'has_next': has_next,
            'praat': praat_feature
        }
    
    async def get_item_by_index(
        self,
        session_id: int,
        user_id: int,
        item_index: int
    ):
        """특정 인덱스의 아이템 조회 (세션 상태 무관). Eager Loading된 데이터를 활용합니다."""
        session = await self.get_training_session(session_id, user_id)
        if not session:
            return None

        # Eager Loading으로 이미 로드된 training_items 리스트에서 해당 인덱스의 아이템을 찾습니다.
        # 이렇게 하면 추가 DB 조회를 방지할 수 있습니다.
        item = next((i for i in session.training_items if i.item_index == item_index), None)
        if not item:
            return None

        # 총 아이템 수 기준으로 다음 아이템 존재 여부 판단 (완료 여부 무관)
        has_next = item_index < (session.total_items - 1)

        # Praat 분석 결과 조회 시도
        praat_feature = None
        try:
            # item.media_file은 Eager Loading으로 이미 로드되어 있습니다.
            media_file = item.media_file
            if media_file:
                # VOCAL 타입: media_file_id가 이미 오디오를 가리킴
                # WORD/SENTENCE 타입: media_file_id는 비디오를 가리키므로 .mp4 -> .wav 치환 필요
                if session.type == TrainingType.VOCAL:
                    # VOCAL: media_file_id가 이미 오디오 media_id
                    praat_feature = await self.praat_repo.get_by_media_id(media_file.id)
                else:
                    # WORD/SENTENCE: video media에서 audio media 찾기
                    if media_file.object_key and media_file.object_key.endswith('.mp4'):
                        audio_object_key = media_file.object_key.replace('.mp4', '.wav')
                        media_service = MediaService(self.db)
                        audio_media = await media_service.get_media_file_by_object_key(audio_object_key)
                        if audio_media:
                            praat_feature = await self.praat_repo.get_by_media_id(audio_media.id)
        except Exception as e:
            # praat 조회 실패는 무시하고 None 반환
            print(f"Praat 조회 중 예외 발생: {e}")

        return {
            'item': item,
            'has_next': has_next,
            'praat': praat_feature
        }
    
    async def delete_training_session(
        self, 
        session_id: int, 
        user_id: int
    ) -> bool:
        """훈련 세션 삭제"""
        return await self.repo.delete_session(session_id, user_id)
    
    async def get_item_with_media(self, session_id: int, item_id: int, user_id: int):
        """아이템과 연결된 미디어 조회 (서명 URL 발급용)"""
        # 세션 소유권 확인
        session = await self.get_training_session(session_id, user_id)
        if not session:
            return None
        # 아이템 조회
        item = await self.item_repo.get_item(session_id, item_id, include_relations=False)
        if not item:
            return None
        media = None
        if item.media_file_id:
            from ..services.media import MediaService
            media_service = MediaService(self.db)
            media = await media_service.get_media_file_by_id(item.media_file_id)
        return {"item": item, "media": media}

    async def get_media_file_by_id(self, media_file_id: int) -> Optional[MediaFile]:
        """미디어 파일 ID로 조회"""
        from ..services.media import MediaService
        media_service = MediaService(self.db)
        return await media_service.get_media_file_by_id(media_file_id)
    
    def _is_valid_status_transition(
        self, 
        current_status: TrainingSessionStatus, 
        new_status: TrainingSessionStatus
    ) -> bool:
        """상태 전환 유효성 검증"""
        valid_transitions = {
            TrainingSessionStatus.IN_PROGRESS: [
                TrainingSessionStatus.COMPLETED,
                TrainingSessionStatus.PAUSED
            ],
            TrainingSessionStatus.COMPLETED: [],  # 완료된 세션은 상태 변경 불가
            TrainingSessionStatus.PAUSED: []   # 일시중지된 세션은 상태 변경 불가
        }
        
        return new_status in valid_transitions.get(current_status, [])
    
    async def retry_completed_session(
        self,
        session_id: int,
        user_id: int,
        session_name: Optional[str] = None
    ) -> TrainingSession:
        """완료된 세션을 똑같은 단어/문장으로 재훈련 세션 생성"""
        # 기존 세션 조회
        original_session = await self.get_training_session(session_id, user_id)
        if not original_session:
            raise LookupError("훈련 세션을 찾을 수 없습니다.")
        
        # 완료된 세션인지 확인
        if original_session.status != TrainingSessionStatus.COMPLETED:
            raise ValueError("완료된 세션만 재훈련할 수 있습니다.")
        
        # 기존 세션의 모든 훈련 아이템 조회
        items = original_session.training_items
        if not items:
            raise ValueError("훈련 아이템이 없습니다.")
        
        # 훈련 아이템에서 word_id 또는 sentence_id 추출 (순서 유지)
        item_ids = []
        for item in sorted(items, key=lambda x: x.item_index):
            if original_session.type == TrainingType.WORD and item.word_id:
                item_ids.append(item.word_id)
            elif original_session.type == TrainingType.SENTENCE and item.sentence_id:
                item_ids.append(item.sentence_id)
        
        if not item_ids:
            raise ValueError("재훈련할 아이템을 찾을 수 없습니다.")
        
        # 새 세션 이름 생성 (지정되지 않은 경우)
        new_session_name = session_name or f"{original_session.session_name} (재훈련)"
        
        # 새 훈련 세션 생성
        new_session = await self.repo.create_session(
            user_id=user_id,
            session_name=new_session_name,
            type=original_session.type,
            total_items=len(item_ids),
            training_date=None,  # 현재 날짜로 설정됨
            session_metadata={"retried_from": session_id, **original_session.session_metadata}
        )
        
        # 동일한 순서로 훈련 아이템들 생성
        await self.item_repo.create_batch(
            new_session.id,
            item_ids,
            original_session.type
        )
        
        await self.db.commit()
        return new_session
    
    async def submit_vocal_item(
        self,
        *,
        session_id: int,
        item_index: int,
        user: User,
        audio_file_bytes: bytes,
        graph_image_bytes: bytes,
        audio_filename: str,
        image_filename: str,
        audio_content_type: str,
        image_content_type: str,
        graph_video_bytes: Optional[bytes] = None,
        graph_video_filename: Optional[str] = None,
        graph_video_content_type: Optional[str] = None,
        gcs_service: GCSService
    ) -> Dict[str, Any]:
        """발성 훈련 아이템 제출 (오디오 + 그래프 이미지 업로드, 그래프 영상은 선택사항)"""
        start_time = time.time()
        # 1. 세션 확인 및 타입 검증
        session = await self.get_training_session(session_id, user.id)
        if not session:
            raise LookupError("훈련 세션을 찾을 수 없습니다.")
        
        if session.type != TrainingType.VOCAL:
            raise ValueError("해당 세션은 VOCAL 타입이 아닙니다.")
        
        # 2. 아이템 조회
        item = await self.item_repo.get_item_by_index(session_id, item_index, include_relations=True)
        if not item:
            raise LookupError(f"해당 인덱스({item_index})의 아이템을 찾을 수 없습니다.")
        
        if item.is_completed:
            raise ValueError("이미 완료된 아이템입니다.")
        
        # 3. 오디오 파일 GCS 업로드
        audio_object_key = f"audios/{user.username}/{session_id}/audio_item_{item.id}.wav"
        audio_blob = gcs_service.bucket.blob(audio_object_key)
        audio_blob.upload_from_string(
            audio_file_bytes,
            content_type=audio_content_type
        )
        audio_blob.metadata = {
            "username": user.username,
            "session_id": str(session_id),
            "item_id": str(item.id),
            "upload_date": datetime.now().isoformat(),
            "file_type": "audio"
        }
        audio_blob.patch()
        
        # 오디오 파일에 대한 서명 URL 생성
        audio_url = await gcs_service.get_signed_url(audio_object_key, expiration_hours=24)
        if not audio_url:
            raise RuntimeError("오디오 파일 URL 생성에 실패했습니다.")
        
        # 4. 그래프 이미지 GCS 업로드
        from api.shared.utils.file_utils import sanitize_username_for_path
        safe_username = sanitize_username_for_path(user.username)
        # 이미지 파일 확장자 추출
        image_ext = image_filename.split('.')[-1] if '.' in image_filename else "png"
        image_object_key = f"images/{safe_username}/{session_id}/graph_item_{item_index}.{image_ext}"
        image_blob = gcs_service.bucket.blob(image_object_key)
        image_blob.upload_from_string(
            graph_image_bytes,
            content_type=image_content_type
        )
        image_blob.metadata = {
            "username": user.username,
            "session_id": str(session_id),
            "item_id": str(item.id),
            "item_index": str(item_index),
            "upload_date": datetime.now().isoformat(),
            "file_type": "image"
        }
        image_blob.patch()
        
        # 그래프 이미지에 대한 서명 URL 생성
        image_url = await gcs_service.get_signed_url(image_object_key, expiration_hours=24)
        if not image_url:
            raise RuntimeError("그래프 이미지 URL 생성에 실패했습니다.")
        
        # 4-1. 그래프 영상 GCS 업로드 (선택사항)
        video_media_file = None
        video_url = ""
        if graph_video_bytes:
            video_upload_result = await gcs_service.upload_video(
                file_content=graph_video_bytes,
                username=user.username,
                session_id=str(session_id),
                item_index=item_index,
                original_filename=graph_video_filename or "graph.mp4",
                content_type=graph_video_content_type or "video/mp4"
            )
            
            if not video_upload_result.get("success"):
                print(f"[VOCAL] 경고: 그래프 영상 업로드 실패 - {video_upload_result.get('error')}")
                logger.warning(f"[submit_vocal_item] 경고: 그래프 영상 업로드 실패 - {video_upload_result.get('error')}")
            else:
                video_object_key = video_upload_result.get("object_path")
                if video_object_key:
                    video_url = await gcs_service.get_signed_url(video_object_key, expiration_hours=24)
                    if video_url:
                        video_media_file = await self.media_repo.create_and_flush(
                            user_id=user.id,
                            object_key=video_object_key,
                            media_type=MediaType.VIDEO,
                            file_name=video_upload_result.get("filename") or (graph_video_filename or "graph.mp4"),
                            file_size_bytes=len(graph_video_bytes),
                            format=(graph_video_content_type.split('/')[-1] if graph_video_content_type and '/' in graph_video_content_type else "mp4")
                        )
        
        # 5. 오디오 및 이미지 미디어 파일 정보 DB 저장
        audio_media_file = await self.media_repo.create_and_flush(
            user_id=user.id,
            object_key=audio_object_key,
            media_type=MediaType.AUDIO,
            file_name=audio_object_key.split('/')[-1],
            file_size_bytes=len(audio_file_bytes),
            format="wav"
        )
        
        image_media_file = await self.media_repo.create_and_flush(
            user_id=user.id,
            object_key=image_object_key,
            media_type=MediaType.IMAGE,
            file_name=image_object_key.split('/')[-1],
            file_size_bytes=len(graph_image_bytes),
            format=(image_content_type.split('/')[-1] if '/' in image_content_type else image_ext)
        )
        
        # 6. Praat 분석 수행
        praat_feature = None
        try:
            print(f"[VOCAL] Praat 분석 시작 - item_id: {item.id}")
            logger.info(f"[submit_vocal_item] Praat 분석 시작 - item_id: {item.id}")
            praat_data = await extract_all_features(audio_file_bytes)
            print(f"[VOCAL] Praat 분석 완료")
            
            # PraatFeatures DB 저장 (개별 오디오 파일 분석 결과)
            praat_feature = await self.praat_repo.create_and_flush(
                media_id=audio_media_file.id,
                **praat_data
            )
            print(f"[VOCAL] Praat DB 저장 완료 - praat_id: {praat_feature.id}")
            logger.info(f"[submit_vocal_item] Praat DB 저장 완료 - praat_id: {praat_feature.id}")
        except Exception as e:
            print(f"[VOCAL] Praat 분석 실패: {str(e)}")
            import traceback
            traceback.print_exc()
            logger.error(f"[submit_vocal_item] Praat 분석 실패: {e}", exc_info=True)
            # Praat 분석 실패해도 아이템 완료는 계속 진행
        
        # VOCAL 타입은 발성 훈련이므로 STT 불필요
        # 7. 아이템 완료 처리 (이미지 URL 저장, video_url은 선택사항)
        await self.item_repo.complete_item(
            item_id=item.id,
            video_url=video_url,  # graph_video가 제공된 경우에만 값이 있음
            media_file_id=audio_media_file.id,  # 오디오 파일을 media_file_id로 저장
            is_completed=True,
            audio_url=audio_url,
            image_url=image_url  # 이미지는 image_url로만 저장
        )
        
        # 8. 세션 진행률 업데이트
        completed_count = await self.repo.get_completed_items_count(session_id)
        await self.repo.update_progress(session_id, completed_count)
        await self.repo.move_to_next_item(session_id)
        
        await self.db.commit()
        await self.db.refresh(audio_media_file)
        await self.db.refresh(image_media_file)
        if video_media_file:
            await self.db.refresh(video_media_file)
        if praat_feature:
            await self.db.refresh(praat_feature)
            # Commit 후 Praat 데이터 저장 확인
            print(f"[VOCAL] ✅ Commit 완료 - PraatFeatures 확인 (id: {praat_feature.id}, media_id: {praat_feature.media_id})")
        else:
            print(f"[VOCAL] ⚠️ PraatFeatures가 저장되지 않았습니다. (item_id: {item.id}, media_id: {audio_media_file.id})")
        
        # 9. 업데이트된 세션 및 다음 아이템 조회
        updated_session = await self.get_training_session(session_id, user.id)
        next_item = await self.item_repo.get_item_by_index(session_id, item_index + 1, include_relations=True)
        has_next = next_item is not None
        
        elapsed_time = time.time() - start_time
        logger.info(f"[submit_vocal_item] 완료 - session_id: {session_id}, item_index: {item_index}. (총 소요 시간: {elapsed_time:.2f}초)")
        
        return {
            "session": updated_session,
            "next_item": next_item,
            "media_file": audio_media_file,  # 응답에는 오디오 파일 정보 반환
            "praat_feature": praat_feature,
            "stt_result": None,  # STT는 백그라운드 처리이므로 응답에 포함되지 않음
            "video_url": video_url,  # graph_video가 제공된 경우에만 값이 있음
            "audio_url": audio_url,
            "image_url": image_url,
            "video_image_url": video_url,  # graph_video URL (video_url과 동일)
            "has_next": has_next
        }
    
    async def get_vocal_results_summary(
        self,
        session_id: int,
        user_id: int
    ) -> Optional[Dict[str, Any]]:
        """VOCAL 타입 세션의 평균 Praat 결과 조회
        
        평균 계산 규칙:
        - n = total_items / 5 (프론트에서 "아~" 발음 반복 횟수)
        - jitter, shimmer: 처음 n개 아이템 (index 0 ~ n-1)의 평균
        - 나머지 지표: 전체 아이템의 평균
        
        예시: total_items=15면 n=3
        - jitter, shimmer: 아이템 0, 1, 2의 평균
        - 나머지: 전체 15개의 평균
        
        Returns:
            세션 정보와 평균 Praat 결과를 포함한 딕셔너리
        """
        # 세션 조회 및 소유권 확인
        session = await self.get_training_session(session_id, user_id)
        if not session:
            return None
        
        # VOCAL 타입 확인
        if session.type != TrainingType.VOCAL:
            raise ValueError("이 API는 VOCAL 타입 세션에서만 사용할 수 있습니다.")
        
        # 아이템별 Praat 결과 조회하여 직접 평균 계산
        items_with_praat = await self.session_praat_repo.get_session_items_with_praat(session_id)
        
        # Praat 데이터가 있는 아이템만 필터링
        praat_list = [(item, praat) for item, praat in items_with_praat if praat is not None]
        
        # 실제 아이템 수 기준으로 n 계산 (total_items가 아닌 실제 제출된 아이템 수)
        actual_items_count = len(praat_list)
        
        if actual_items_count == 0:
            raise ValueError("Praat 데이터가 있는 아이템이 없습니다.")
        
        if actual_items_count % 5 != 0:
            raise ValueError(f"제출된 아이템 수({actual_items_count})가 5의 배수가 아닙니다.")
        
        n = actual_items_count // 5
        
        # 평균 계산 헬퍼 함수
        def calc_avg(values: List[Optional[float]]) -> Optional[float]:
            """None이 아닌 값들의 평균 계산"""
            valid_values = [v for v in values if v is not None]
            if not valid_values:
                return None
            return sum(valid_values) / len(valid_values)
        
        # jitter, shimmer: 처음 n개 아이템 (index 0 ~ n-1)의 평균
        first_n_items = [praat for item, praat in praat_list if item.item_index < n]
        avg_jitter_local = calc_avg([p.jitter_local for p in first_n_items])
        avg_shimmer_local = calc_avg([p.shimmer_local for p in first_n_items])
        
        # 나머지: 전체 아이템의 평균
        all_items = [praat for _, praat in praat_list]
        avg_nhr = calc_avg([p.nhr for p in all_items])
        avg_hnr = calc_avg([p.hnr for p in all_items])
        avg_lh_ratio_mean_db = calc_avg([p.lh_ratio_mean_db for p in all_items])
        avg_lh_ratio_sd_db = calc_avg([p.lh_ratio_sd_db for p in all_items])
        avg_max_f0 = calc_avg([p.max_f0 for p in all_items])
        avg_min_f0 = calc_avg([p.min_f0 for p in all_items])
        avg_intensity_mean = calc_avg([p.intensity_mean for p in all_items])
        avg_f0 = calc_avg([p.f0 for p in all_items])
        avg_f1 = calc_avg([p.f1 for p in all_items])
        avg_f2 = calc_avg([p.f2 for p in all_items])
        
        # 결과 객체 생성
        from ..models.session_praat_result import SessionPraatResult
        avg_result = SessionPraatResult(
            training_session_id=session_id,
            avg_jitter_local=avg_jitter_local,
            avg_shimmer_local=avg_shimmer_local,
            avg_nhr=avg_nhr,
            avg_hnr=avg_hnr,
            avg_lh_ratio_mean_db=avg_lh_ratio_mean_db,
            avg_lh_ratio_sd_db=avg_lh_ratio_sd_db,
            avg_max_f0=avg_max_f0,
            avg_min_f0=avg_min_f0,
            avg_intensity_mean=avg_intensity_mean,
            avg_f0=avg_f0,
            avg_f1=avg_f1,
            avg_f2=avg_f2
        )
        
        return {
            "session_id": session.id,
            "session_name": session.session_name,
            "total_items": session.total_items,
            "completed_items": session.completed_items,
            "average_results": avg_result
        }
    
    async def get_vocal_results_detail(
        self,
        session_id: int,
        user_id: int
    ) -> Optional[Dict[str, Any]]:
        """VOCAL 타입 세션의 아이템별 상세 Praat 결과 조회
        
        Returns:
            세션 정보와 각 아이템별 Praat 결과를 포함한 딕셔너리
        """
        # 세션 조회 및 소유권 확인
        session = await self.get_training_session(session_id, user_id)
        if not session:
            return None
        
        # VOCAL 타입 확인
        if session.type != TrainingType.VOCAL:
            raise ValueError("이 API는 VOCAL 타입 세션에서만 사용할 수 있습니다.")
        
        # 아이템별 Praat 결과 조회
        items_with_praat = await self.session_praat_repo.get_session_items_with_praat(session_id)
        
        # 응답 형식으로 변환
        items_detail = []
        for item, praat_feature in items_with_praat:
            items_detail.append({
                "item_index": item.item_index,
                "item_id": item.id,
                "praat_features": praat_feature
            })
        
        return {
            "session_id": session.id,
            "session_name": session.session_name,
            "total_items": session.total_items,
            "completed_items": session.completed_items,
            "items": items_detail
        }