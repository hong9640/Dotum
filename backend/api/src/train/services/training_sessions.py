from fastapi import BackgroundTasks
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from datetime import datetime, date

from ..models.training_session import TrainingSession, TrainingType, TrainingSessionStatus
from ..repositories.training_sessions import TrainingSessionRepository
from ..repositories.training_items import TrainingItemRepository
from ..repositories.media import MediaRepository
from ..repositories.praat import PraatRepository
from ..schemas.training_sessions import (
    TrainingSessionCreate,
    TrainingSessionUpdate,
    TrainingSessionResponse,
    TrainingSessionStatusUpdate,
    CalendarResponse,
    DailyTrainingResponse
)
from ..models.media import MediaFile, MediaType
from ..services.gcs_service import GCSService
from ..services.video_processor import VideoProcessor
from ..services.media import MediaService
from ..services.text_to_speech import TextToSpeechService
from ..services.praat import get_praat_analysis_from_db
from ..services.praat_service import save_session_praat_result
from api.src.user.user_model import User
from api.core.config import settings

class TrainingSessionService:
    """통합된 훈련 세션 서비스"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = TrainingSessionRepository(db)
        self.item_repo = TrainingItemRepository(db)
        self.media_repo = MediaRepository(db)
        self.praat_repo = PraatRepository(db)
    
    async def create_training_session(
        self, 
        user_id: int, 
        session_data: TrainingSessionCreate
    ) -> TrainingSession:
        """훈련 세션 생성"""
        # 랜덤 아이템 ID들 가져오기
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
        
        # 세션 상태를 완료로 변경
        await self.repo.update_status(
            session_id, 
            TrainingSessionStatus.COMPLETED,
            user_id
        )
        await self.db.commit()
        
        # vocal 타입 세션의 경우 Praat 평균 결과 저장 (이미 조회한 세션 객체 전달하여 재조회 방지)
        try:
            await save_session_praat_result(self.db, session_id, session)
        except Exception as e:
            # Praat 평균 계산 실패해도 세션 완료는 정상 처리
            print(f"⚠️ Session {session_id}: Praat 평균 결과 저장 실패: {e}")
        
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
    
    async def trigger_wav2lip_processing(
        self,
        text: str,
        user_video_gs_path: str,
        output_video_gs_path: str,
        user_id: int,
        output_object_key: str
    ):
        """외부 wav2lip 서버에 처리를 요청하는 백그라운드 작업"""
        WAV2LIP_API_URL = f"{settings.ML_SERVER_URL}/api/v1/lip-video"
        
        payload = {
            "word": text,
            "user_video_gs": f"gs://{user_video_gs_path}",
            "output_video_gs": f"gs://{output_video_gs_path}"
        }

        try:
            # 외부 API 호출 (httpx 라이브러리 필요)
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(WAV2LIP_API_URL, json=payload)
                response.raise_for_status()
                print(f"wav2lip 작업 요청 성공: {response.json()}")

                gcs_service = GCSService(settings)

                # 2. GCS에서 결과 파일의 메타데이터(정보) 가져오기
                blob = gcs_service.bucket.get_blob(output_object_key)
                file_size = 0
                if blob:
                    file_size = blob.size # 파일 크기(bytes)
                else:
                    print(f"경고: GCS에서 {output_object_key} 파일을 찾을 수 없어 파일 크기를 0으로 저장합니다.")

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
                print(f"wav2lip 결과 미디어 파일 정보 저장 성공: {result_media_file.id}")

        except httpx.RequestError as e:
            print(f"wav2lip 작업 요청 실패: {e}")
        except Exception as e:
            print(f"wav2lip 결과 저장 중 DB 오류 발생: {e}")
    
    async def trigger_guide_audio_generation(
        self,
        *,
        user: User,
        session_id: int,
        item_id: int,
        text: str,
        original_audio_object_key: str,
        gcs_service: GCSService
    ):
        """백그라운드 작업: 원본 음성을 복제하여 가이드 음성을 생성하고 GCS에 저장"""
        try:
            print(f"[GUIDE] 가이드 음성 생성 시작 - item_id: {item_id}")
            
            # 1. GCS에서 원본 음성 파일 다운로드
            original_audio_bytes = await gcs_service.download_video(original_audio_object_key)
            if not original_audio_bytes:
                print(f"[GUIDE] 원본 음성 다운로드 실패: {original_audio_object_key}")
                return

            # 2. 텍스트와 음성 샘플로 MP3 음성 생성 (음성 복제)
            tts_service = TextToSpeechService()
            mp3_bytes = await tts_service.generate_guide_audio(
                text=text, audio_sample_bytes=original_audio_bytes
            )
            if not mp3_bytes:
                print(f"[GUIDE] 가이드 음성(MP3) 생성 실패 - item_id: {item_id}")
                return

            # 3. MP3를 WAV로 변환
            video_processor = VideoProcessor()
            wav_bytes = await video_processor.convert_mp3_to_wav(mp3_bytes)
            if not wav_bytes:
                print(f"[GUIDE] 가이드 음성(WAV) 변환 실패 - item_id: {item_id}")
                return

            # 4. GCS에 '가이드 음성'을 다른 이름으로 업로드
            guide_audio_object_key = f"guides/{user.username}/{session_id}/guide_item_{item_id}.wav"
            guide_audio_blob = gcs_service.bucket.blob(guide_audio_object_key)
            guide_audio_blob.upload_from_string(wav_bytes, content_type="audio/wav")
            print(f"[GUIDE] 가이드 음성 GCS 업로드 성공: {guide_audio_object_key}")

            # 5. MediaFile DB에 '가이드 음성' 정보 저장
            await self.media_repo.create_and_flush(
                user_id=user.id,
                object_key=guide_audio_object_key,
                media_type=MediaType.AUDIO,
                file_name=guide_audio_object_key.split('/')[-1],
                file_size_bytes=len(wav_bytes),
                format="wav"
            )
            await self.db.commit()
            print(f"[GUIDE] 가이드 음성 DB 저장 성공")

        except Exception as e:
            await self.db.rollback()
            print(f"[GUIDE] 가이드 음성 생성/저장 중 오류 발생: {e}")

    async def _submit_item_with_video(
        self,
        *,
        session_id: int,
        item_id: int,
        user: User,
        file_bytes: bytes,
        filename: str,
        content_type: str,
        gcs_service: GCSService,
        background_tasks: BackgroundTasks
    ) -> Dict[str, Any]:
        """내부 메서드: 특정 아이템에 동영상 업로드 및 완료 처리"""
        print(f"[WAV] ========== _submit_item_with_video 메서드 시작 - session_id: {session_id}, item_id: {item_id} ==========")
        session = await self.get_training_session(session_id, user.id)
        if not session:
            raise LookupError("훈련 세션을 찾을 수 없습니다.")
        
        item = await self.item_repo.get_item(session_id, item_id, include_relations=True)
        if not item:
            raise LookupError("훈련 아이템을 찾을 수 없습니다.")
        
        if item.is_completed:
            raise ValueError("이미 완료된 아이템입니다.")
        
        upload_result = await gcs_service.upload_video(
            file_content=file_bytes,
            username=user.username,
            session_id=str(session_id),
            train_id=item.id,  # 아이템 ID를 train_id로 사용
            word_id=item.word_id,
            sentence_id=item.sentence_id,
            original_filename=filename,
            content_type=content_type
        )
        
        if not upload_result.get("success"):
            raise RuntimeError(f"동영상 업로드에 실패했습니다: {upload_result.get('error')}")
        
        object_key = upload_result.get("object_path")
        if not object_key:
            raise RuntimeError("업로드 결과에 object_path가 없습니다.")
        
        # Private 버킷이므로 signed URL 생성
        video_url = await gcs_service.get_signed_url(object_key, expiration_hours=24)
        if not video_url:
            raise RuntimeError("동영상 URL 생성에 실패했습니다.")
        if item.word or item.sentence:
            text_to_process = item.word.word if item.word else item.sentence.sentence
            output_object_key = f"results/{user.username}/{session_id}/result_item_{item.id}.mp4"
            user_video_full_path = f"{gcs_service.bucket_name}/{object_key}"
            output_video_full_path = f"{gcs_service.bucket_name}/{output_object_key}"

            background_tasks.add_task(
                self.trigger_wav2lip_processing,
                text=text_to_process,
                user_video_gs_path=user_video_full_path,
                output_video_gs_path=output_video_full_path,
                user_id=user.id,
                output_object_key=output_object_key
            )
        
        # 동영상 파일 정보 저장
        media_file = await self.media_repo.create_and_flush(
            user_id=user.id,
            object_key=object_key,
            media_type=MediaType.VIDEO,
            file_name=upload_result.get("filename") or filename,
            file_size_bytes=len(file_bytes),
            format=(content_type.split('/')[-1] if '/' in content_type else content_type)
        )
        print(f"[WAV] ========== 동영상 저장 완료, 이제 음성 추출 시작 ==========")
        
        # 음성 추출 및 저장
        audio_media_file = None
        new_praat_record = None
        try:
            print(f"[WAV] 음성 처리 시작 - video: {object_key}")
            # VideoProcessor를 사용하여 음성 추출
            video_processor = VideoProcessor()
            processing_result = await video_processor.process_uploaded_video_with_audio(
                gcs_bucket=gcs_service.bucket_name,
                gcs_blob_name=object_key
            )
            print(f"[WAV] 음성 처리 완료 - audio_blob_name: {processing_result.get('audio_blob_name')}")
            
            praat_data = processing_result.get('praat_features')
            # 음성 파일 정보 저장
            if processing_result.get('audio_blob_name'):
                print(f"[WAV] DB 저장 시작 - audio_blob_name: {processing_result['audio_blob_name']}")
                audio_media_file = await self.media_repo.create_and_flush(
                    user_id=user.id,
                    object_key=processing_result['audio_blob_name'],
                    media_type=MediaType.AUDIO,
                    file_name=processing_result['audio_blob_name'].split('/')[-1],
                    file_size_bytes=0,  # 크기는 나중에 업데이트
                    format="wav"
                )
                print(f"[WAV] DB 저장 완료 - media_id: {audio_media_file.id}")
            else:
                print(f"[WAV] 경고: audio_blob_name이 없습니다")
            
            if praat_data and audio_media_file:
                print(f"[WAV] Praat DB 저장 - media_id: {audio_media_file.id}")
                new_praat_record = await self.praat_repo.create_and_flush(
                    media_id=audio_media_file.id,
                    **praat_data
                )
                print(f"[WAV] Praat DB 저장 완료 - praat_id: {new_praat_record.id}")

        except Exception as e:
            # 음성 추출 실패해도 동영상 업로드는 계속 진행
            print(f"[WAV] Audio extraction failed: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # 가이드 음성 생성을 위한 백그라운드 작업 추가
        if (item.word or item.sentence) and audio_media_file:
            text_for_guide = item.word.word if item.word else item.sentence.sentence
            background_tasks.add_task(
                self.trigger_guide_audio_generation,
                user=user,
                session_id=session_id,
                item_id=item.id,
                text=text_for_guide,
                original_audio_object_key=audio_media_file.object_key,
                gcs_service=gcs_service
            )

        await self.item_repo.complete_item(
            item_id=item.id,
            video_url=video_url,
            media_file_id=media_file.id,
            is_completed=True
        )
        
        completed_count = await self.repo.get_completed_items_count(session_id)
        await self.repo.update_progress(session_id, completed_count)
        await self.repo.move_to_next_item(session_id)
        
        await self.db.commit()
        await self.db.refresh(media_file)
        if audio_media_file:
            await self.db.refresh(audio_media_file)
        
        updated_session = await self.get_training_session(session_id, user.id)
        next_item = await self.item_repo.get_current_item(session_id, include_relations=True)
        has_next = False
        if next_item:
            has_next = await self.item_repo.get_next_item(session_id, next_item.item_index) is not None
        
        return {
            "session": updated_session,
            "next_item": next_item,
            "media_file": media_file,
            "praat_feature": new_praat_record,
            "audio_media_file": audio_media_file,
            "video_url": video_url,
            "has_next": has_next
        }
    
    async def submit_current_item_with_video(
        self,
        *,
        session_id: int,
        user: User,
        file_bytes: bytes,
        filename: str,
        content_type: str,
        gcs_service: GCSService,
        background_tasks: BackgroundTasks
    ) -> Dict[str, Any]:
        """현재 진행 중인 아이템에 동영상 업로드 및 완료 처리"""
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
        return await self._submit_item_with_video(
            session_id=session_id,
            item_id=current_item.id,
            user=user,
            file_bytes=file_bytes,
            filename=filename,
            content_type=content_type,
            gcs_service=gcs_service,
            background_tasks=background_tasks
        )
    
    async def resubmit_item_video(
        self,
        *,
        session_id: int,
        item_id: int,
        user: User,
        file_bytes: bytes,
        filename: str,
        content_type: str,
        gcs_service: GCSService
    ) -> Dict[str, Any]:
        """특정 아이템의 동영상을 재업로드(덮어쓰기).
        완료된 아이템도 허용하며 진행률/포인터는 변경하지 않는다.
        같은 경로에 새 파일을 업로드하여 기존 파일을 덮어쓴다.
        """
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

        # 같은 경로에 새 동영상 업로드 (덮어쓰기)
        upload_result = await gcs_service.upload_video(
            file_content=file_bytes,
            username=user.username,
            session_id=str(session_id),
            train_id=item.id,
            word_id=item.word_id,
            sentence_id=item.sentence_id,
            original_filename=filename,
            content_type=content_type
        )

        if not upload_result.get("success"):
            raise RuntimeError(f"동영상 업로드에 실패했습니다: {upload_result.get('error')}")

        object_key = upload_result.get("object_path")
        if not object_key:
            raise RuntimeError("업로드 결과에 object_path가 없습니다.")

        video_url = await gcs_service.get_signed_url(object_key, expiration_hours=24)
        if not video_url:
            raise RuntimeError("동영상 URL 생성에 실패했습니다.")

        # 기존 미디어 파일이 있으면 업데이트, 없으면 새로 생성
        if old_media_file:
            # 기존 미디어 파일 정보 업데이트
            media_file = await self.media_repo.update_media_file(
                media_file=old_media_file,
                file_name=upload_result.get("filename") or filename,
                file_size_bytes=len(file_bytes),
                format=content_type.split('/')[-1] if '/' in content_type else content_type
            )
        else:
            # 새 미디어 파일 생성
            media_file = await self.media_repo.create_and_flush(
                user_id=user.id,
                object_key=object_key,
                media_type=MediaType.VIDEO,
                file_name=upload_result.get("filename") or filename,
                file_size_bytes=len(file_bytes),
                format=(content_type.split('/')[-1] if '/' in content_type else content_type)
            )

        audio_media_file = None
        new_praat_record = None
        try:
            print(f"[WAV] 재업로드 - 음성 처리 시작 - video: {object_key}")
            video_processor = VideoProcessor()
            processing_result = await video_processor.process_uploaded_video_with_audio(
                gcs_bucket=gcs_service.bucket_name,
                gcs_blob_name=object_key
            )
            print(f"[WAV] 재업로드 - 음성 처리 완료 - audio_blob_name: {processing_result.get('audio_blob_name')}")
            
            if processing_result.get('audio_blob_name'):
                from ..services.media import MediaService
                media_service = MediaService(self.db)
                existing_audio = await media_service.get_media_file_by_object_key(processing_result['audio_blob_name'])
                if existing_audio:
                    print(f"[WAV] 재업로드 - 기존 DB 레코드 업데이트 - media_id: {existing_audio.id}")
                    # 메타데이터 갱신만 수행
                    audio_media_file = await self.media_repo.update_media_file(
                        media_file=existing_audio,
                        file_name=processing_result['audio_blob_name'].split('/')[-1],
                        format="wav"
                    )
                else:
                    print(f"[WAV] 재업로드 - 새 DB 레코드 생성")
                    audio_media_file = await self.media_repo.create_and_flush(
                        user_id=user.id,
                        object_key=processing_result['audio_blob_name'],
                        media_type=MediaType.AUDIO,
                        file_name=processing_result['audio_blob_name'].split('/')[-1],
                        file_size_bytes=0,
                        format="wav"
                    )
                print(f"[WAV] 재업로드 - DB 저장 완료 - media_id: {audio_media_file.id}")

                # Praat 분석 결과 생성 또는 업데이트
                praat_data = processing_result.get('praat_features')
                if praat_data and audio_media_file:
                    # 기존 분석 결과가 있는지 확인
                    existing_praat = await self.praat_repo.get_by_media_id(audio_media_file.id)
                    if existing_praat:
                        print(f"[WAV] 재업로드 - Praat DB 업데이트 - praat_id: {existing_praat.id}")
                        # 1. 업데이트할 객체의 속성을 직접 변경
                        for key, value in praat_data.items():
                            setattr(existing_praat, key, value)
                        # 2. 변경된 객체를 전달하여 업데이트
                        new_praat_record = await self.praat_repo.update(existing_praat)
                    else:
                        print(f"[WAV] 재업로드 - Praat DB 생성 - media_id: {audio_media_file.id}")
                        new_praat_record = await self.praat_repo.create_and_flush(
                            media_id=audio_media_file.id,
                            **praat_data
                        )
                    print(f"[WAV] 재업로드 - Praat DB 처리 완료 - praat_id: {new_praat_record.id}")

            else:
                print(f"[WAV] 재업로드 - 경고: audio_blob_name이 없습니다")
        except Exception as e:
            print(f"[WAV] 재업로드 - Audio extraction failed: {str(e)}")
            import traceback
            traceback.print_exc()

        # 아이템의 동영상 정보 업데이트 (완료 상태 유지)
        await self.item_repo.complete_item(
            item_id=item.id,
            video_url=video_url,
            media_file_id=media_file.id,
            is_completed=True
        )

        await self.db.commit()
        await self.db.refresh(media_file)
        if audio_media_file:
            await self.db.refresh(audio_media_file)
        if new_praat_record:
            await self.db.refresh(new_praat_record)

        updated_session = await self.get_training_session(session_id, user.id)

        return {
            "session": updated_session,
            "next_item": None,
            "media_file": media_file,
            "praat_feature": new_praat_record,
            "audio_media_file": audio_media_file,
            "video_url": video_url,
            "has_next": False
        }
    
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
                video_media = await self.get_media_file_by_id(current_item.media_file_id)
                if video_media and video_media.object_key and video_media.object_key.endswith('.mp4'):
                    audio_object_key = video_media.object_key.replace('.mp4', '.wav')
                    from ..services.media import MediaService
                    media_service = MediaService(self.db)
                    audio_media = await media_service.get_media_file_by_object_key(audio_object_key)
                    if audio_media:
                        praat_feature = await get_praat_analysis_from_db(self.db, media_id=audio_media.id, user_id=user_id)
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

        # Praat 분석 결과 조회 시도: 비디오 media의 object_key를 .wav로 치환해 오디오 media 탐색
        praat_feature = None
        try:
            # item.media_file은 Eager Loading으로 이미 로드되어 있습니다.
            video_media = item.media_file
            if video_media and video_media.object_key and video_media.object_key.endswith('.mp4'):
                audio_object_key = video_media.object_key.replace('.mp4', '.wav')
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