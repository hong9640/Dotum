from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from datetime import datetime, date

from ..models.training_session import TrainingSession, TrainingType, TrainingSessionStatus
from ..repositories.training_sessions import TrainingSessionRepository
from ..repositories.training_items import TrainingItemRepository
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
from ..services.video_processor import VideoProcessor
from api.src.user.user_model import User
from api.src.train.models.praat import PraatFeatures

class TrainingSessionService:
    """통합된 훈련 세션 서비스"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = TrainingSessionRepository(db)
        self.item_repo = TrainingItemRepository(db)
    
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
        
        # 세션 상태를 완료로 변경
        await self.repo.update_status(
            session_id, 
            TrainingSessionStatus.COMPLETED,
            user_id
        )
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
    
    async def _submit_item_with_video(
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
        """내부 메서드: 특정 아이템에 동영상 업로드 및 완료 처리"""
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
        
        # 동영상 파일 정보 저장
        media_file = MediaFile(
            user_id=user.id,
            object_key=object_key,
            media_type=MediaType.VIDEO,
            file_name=upload_result.get("filename") or filename,
            file_size_bytes=len(file_bytes),
            format=(content_type.split('/')[-1] if '/' in content_type else content_type)
        )
        self.db.add(media_file)
        await self.db.flush()
        
        # 음성 추출 및 저장
        audio_media_file = None
        try:
            # VideoProcessor를 사용하여 음성 추출
            video_processor = VideoProcessor()
            processing_result = await video_processor.process_uploaded_video_with_audio(
                gcs_bucket=gcs_service.bucket_name,
                gcs_blob_name=object_key
            )
            praat_data = processing_result.get('praat_features')
            # 음성 파일 정보 저장
            if processing_result.get('audio_blob_name'):
                audio_media_file = MediaFile(
                    user_id=user.id,
                    object_key=processing_result['audio_blob_name'],
                    media_type=MediaType.AUDIO,
                    file_name=processing_result['audio_blob_name'].split('/')[-1],
                    file_size_bytes=0,  # 크기는 나중에 업데이트
                    format="wav"
                )
                self.db.add(audio_media_file)
                await self.db.flush()
            
            if praat_data:
                new_praat_record = PraatFeatures(
                    media_id=audio_media_file.id,  
                    
                    # 'praat_data' 딕셔너리 매핑
                    **praat_data  
                )
                self.db.add(new_praat_record)

        except Exception as e:
            # 음성 추출 실패해도 동영상 업로드는 계속 진행
            print(f"Audio extraction failed: {str(e)}")
        
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
        gcs_service: GCSService
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
            gcs_service=gcs_service
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
            old_media_file = await self.get_media_file_by_id(item.media_file_id)

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
            old_media_file.file_name = upload_result.get("filename") or filename
            old_media_file.file_size_bytes = len(file_bytes)
            old_media_file.format = content_type.split('/')[-1] if '/' in content_type else content_type
            old_media_file.updated_at = datetime.now()
            media_file = old_media_file
        else:
            # 새 미디어 파일 생성
            media_file = MediaFile(
                user_id=user.id,
                object_key=object_key,
                media_type=MediaType.VIDEO,
                file_name=upload_result.get("filename") or filename,
                file_size_bytes=len(file_bytes),
                format=(content_type.split('/')[-1] if '/' in content_type else content_type)
            )
            self.db.add(media_file)
            await self.db.flush()

        audio_media_file = None
        try:
            video_processor = VideoProcessor()
            processing_result = await video_processor.process_uploaded_video_with_audio(
                gcs_bucket=gcs_service.bucket_name,
                gcs_blob_name=object_key
            )
            if processing_result.get('audio_blob_name'):
                from ..services.media import MediaService
                media_service = MediaService(self.db)
                existing_audio = await media_service.get_media_file_by_object_key(processing_result['audio_blob_name'])
                if existing_audio:
                    # 메타데이터 갱신만 수행
                    existing_audio.file_name = processing_result['audio_blob_name'].split('/')[-1]
                    existing_audio.format = "wav"
                    existing_audio.updated_at = datetime.now()
                    audio_media_file = existing_audio
                else:
                    audio_media_file = MediaFile(
                        user_id=user.id,
                        object_key=processing_result['audio_blob_name'],
                        media_type=MediaType.AUDIO,
                        file_name=processing_result['audio_blob_name'].split('/')[-1],
                        file_size_bytes=0,
                        format="wav"
                    )
                    self.db.add(audio_media_file)
                    await self.db.flush()
        except Exception as e:
            print(f"Audio extraction failed: {str(e)}")

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

        updated_session = await self.get_training_session(session_id, user.id)

        return {
            "session": updated_session,
            "next_item": None,
            "media_file": media_file,
            "audio_media_file": audio_media_file,
            "video_url": video_url,
            "has_next": False
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
        
        return {
            'item': current_item,
            'has_next': has_next
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
                TrainingSessionStatus.CANCELLED
            ],
            TrainingSessionStatus.COMPLETED: [],  # 완료된 세션은 상태 변경 불가
            TrainingSessionStatus.CANCELLED: []   # 취소된 세션은 상태 변경 불가
        }
        
        return new_status in valid_transitions.get(current_status, [])
