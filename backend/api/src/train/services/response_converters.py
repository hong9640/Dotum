"""
Response converters for training session endpoints.
DB 모델을 API Response 스키마로 변환하는 헬퍼 함수들
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.training_sessions import TrainingSessionResponse
from ..schemas.training_items import CurrentItemResponse, TrainingItemResponse
from ..schemas.media import MediaResponse
from ..schemas.praat import PraatFeaturesResponse
from ..services.training_sessions import TrainingSessionService
from ..services.gcs_service import GCSService
from ..services.media import MediaService


async def get_composited_media_info(
    db: AsyncSession,
    gcs_service: GCSService,
    username: str,
    session_id: int,
    item_id: int
) -> tuple[Optional[str], Optional[int]]:
    """Composited media 정보 조회 (wav2lip 결과)
    
    Returns:
        tuple: (composited_video_url, composited_media_file_id)
    """
    composited_video_url = None
    composited_media_file_id = None
    composited_object_key = f"results/{username}/{session_id}/result_item_{item_id}.mp4"
    
    media_service = MediaService(db)
    composited_media = await media_service.get_media_file_by_object_key(composited_object_key)
    
    if composited_media:
        composited_media_file_id = composited_media.id
        composited_video_url = await gcs_service.get_signed_url(composited_media.object_key, expiration_hours=24)
    
    return composited_video_url, composited_media_file_id


async def build_current_item_response(
    item,
    has_next: bool,
    praat,
    service: TrainingSessionService,
    gcs_service: GCSService,
    username: str,
    session_id: int
) -> CurrentItemResponse:
    """CurrentItemResponse 객체 생성 (중복 제거용 헬퍼)"""
    # 단어 또는 문장 정보 추출
    word = item.word.word if item.word else None
    sentence = item.sentence.sentence if item.sentence else None
    
    # Private 버킷이므로 signed URL 생성
    video_url = None
    if item.video_url and item.media_file_id:
        media_file = await service.get_media_file_by_id(item.media_file_id)
        if media_file:
            video_url = await gcs_service.get_signed_url(media_file.object_key, expiration_hours=24)
    
    # Composited media 조회
    composited_video_url, composited_media_file_id = await get_composited_media_info(
        service.db, gcs_service, username, session_id, item.id
    )
    
    return CurrentItemResponse(
        item_id=item.id,
        item_index=item.item_index,
        word_id=item.word_id,
        sentence_id=item.sentence_id,
        word=word,
        sentence=sentence,
        is_completed=item.is_completed,
        video_url=video_url,
        composited_video_url=composited_video_url,
        media_file_id=item.media_file_id,
        composited_media_file_id=composited_media_file_id,
        has_next=has_next,
        praat=(convert_praat_to_response(praat) if praat else None)
    )


async def convert_training_item_to_response(
    item, 
    db: AsyncSession,
    gcs_service: GCSService,
    username: str,
    session_id: int
) -> Optional[TrainingItemResponse]:
    """TrainingItem 모델을 TrainingItemResponse로 변환"""
    composited_video_url, composited_media_file_id = await get_composited_media_info(
        db, gcs_service, username, session_id, item.id
    )
    
    return TrainingItemResponse(
        item_id=item.id,
        training_session_id=item.training_session_id,
        item_index=item.item_index,
        word_id=item.word_id,
        sentence_id=item.sentence_id,
        word=item.word.word if item.word else None,
        sentence=item.sentence.sentence if item.sentence else None,
        is_completed=item.is_completed,
        video_url=item.video_url,
        media_file_id=item.media_file_id,
        completed_at=item.completed_at,
        created_at=item.created_at,
        updated_at=item.updated_at,
        composited_video_url=composited_video_url,
        composited_media_file_id=composited_media_file_id
    )


async def convert_session_to_response(
    session,
    db: AsyncSession,
    gcs_service: GCSService,
    username: str
) -> TrainingSessionResponse:
    """TrainingSession 모델을 TrainingSessionResponse로 변환"""
    # training_items를 비동기로 변환
    training_items = []
    for item in session.training_items:
        item_response = await convert_training_item_to_response(
            item, db, gcs_service, username, session.id
        )
        training_items.append(item_response)
    
    return TrainingSessionResponse(
        session_id=session.id,
        user_id=session.user_id,
        session_name=session.session_name,
        type=session.type,
        status=session.status,
        training_date=session.training_date,
        total_items=session.total_items,
        completed_items=session.completed_items,
        current_item_index=session.current_item_index,
        progress_percentage=session.progress_percentage,
        session_metadata=session.session_metadata,
        created_at=session.created_at,
        updated_at=session.updated_at,
        started_at=session.started_at,
        completed_at=session.completed_at,
        training_items=training_items
    )


def convert_media_to_response(media) -> MediaResponse:
    """MediaFile 모델을 MediaResponse로 변환"""
    return MediaResponse(
        media_id=media.id,
        user_id=media.user_id,
        object_key=media.object_key,
        media_type=media.media_type,
        file_name=media.file_name,
        file_size_bytes=media.file_size_bytes,
        format=media.format,
        duration_ms=media.duration_ms,
        width_px=media.width_px,
        height_px=media.height_px,
        status=media.status,
        is_public=media.is_public,
        created_at=media.created_at,
        updated_at=media.updated_at
    )


def convert_praat_to_response(praat) -> Optional[PraatFeaturesResponse]:
    """PraatFeatures 모델을 PraatFeaturesResponse로 변환"""
    if praat is None:
        return None
    return PraatFeaturesResponse(
        praat_id=praat.id,
        media_id=praat.media_id,
        jitter_local=praat.jitter_local,
        shimmer_local=praat.shimmer_local,
        hnr=praat.hnr,
        nhr=praat.nhr,
        f0=praat.f0,
        max_f0=praat.max_f0,
        min_f0=praat.min_f0,
        cpp=praat.cpp,
        csid=praat.csid
    )

