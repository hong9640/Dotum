"""
Response converters for training session endpoints.
DB 모델을 API Response 스키마로 변환하는 헬퍼 함수들
"""
import asyncio
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.training_sessions import TrainingSessionResponse
from ..schemas.training_items import CurrentItemResponse, TrainingItemResponse
from ..schemas.media import MediaResponse
from ..schemas.praat import PraatFeaturesResponse, SessionPraatResultResponse
from ..services.training_sessions import TrainingSessionService
from ..services.gcs_service import GCSService
from ..services.media import MediaService

# Sentinel value: "조회하지 않음"을 나타내기 위한 특별한 객체
_NOT_PROVIDED = object()


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
    session_id: int,
    composited_media=_NOT_PROVIDED
) -> CurrentItemResponse:
    """CurrentItemResponse 객체 생성 (중복 제거용 헬퍼)
    
    Args:
        composited_media: 미리 조회한 composited media
            - _NOT_PROVIDED (기본값): 함수 내에서 조회
            - None: 조회했지만 DB에 없음
            - MediaFile 객체: 조회한 결과
    """
    # 단어 또는 문장 정보 추출
    word = item.word.word if item.word else None
    sentence = item.sentence.sentence if item.sentence else None
    
    # 서명된 URL 생성을 위한 task 리스트
    url_tasks = []

    # 1. 원본 비디오 URL 생성 task
    if item.video_url and item.media_file_id:
        # Eager loading으로 이미 로드된 media_file 사용 (DB 조회 방지)
        media_file = item.media_file
        if media_file:
            url_tasks.append(gcs_service.get_signed_url(media_file.object_key, expiration_hours=24))
        else:
            url_tasks.append(asyncio.sleep(0, result=None)) # 순서 유지를 위한 더미
    else:
        url_tasks.append(asyncio.sleep(0, result=None))
    
    # 2. Composited media URL 생성 task
    composited_media_file_id = None
    if composited_media is _NOT_PROVIDED:
        _, composited_media_file_id = await get_composited_media_info(service.db, gcs_service, username, session_id, item.id)
        composited_object_key = f"results/{username}/{session_id}/result_item_{item.id}.mp4"
        url_tasks.append(gcs_service.get_signed_url(composited_object_key, expiration_hours=24))
    elif composited_media:
        composited_media_file_id = composited_media.id
        url_tasks.append(gcs_service.get_signed_url(composited_media.object_key, expiration_hours=24))
    else:
        url_tasks.append(asyncio.sleep(0, result=None))
    
    # 3. 가이드 음성 URL 생성 task
    guide_audio_object_key = f"guides/{username}/{session_id}/guide_item_{item.id}.wav"
    url_tasks.append(gcs_service.get_signed_url(guide_audio_object_key, expiration_hours=24))

    # 모든 URL 요청을 병렬로 실행
    video_url, composited_video_url, integrate_voice_url = await asyncio.gather(*url_tasks, return_exceptions=True)
    # 예외 발생 시 None으로 처리
    video_url = video_url if not isinstance(video_url, Exception) else None
    composited_video_url = composited_video_url if not isinstance(composited_video_url, Exception) else None
    integrate_voice_url = integrate_voice_url if not isinstance(integrate_voice_url, Exception) else None

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
        praat=(await convert_praat_to_response(praat) if praat else None),
        integrate_voice_url=integrate_voice_url
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
        audio_url=item.audio_url,
        image_url=item.image_url,
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
    """TrainingSession 모델을 TrainingSessionResponse로 변환 (session_praat_result 포함, 안전 처리)"""
    from sqlmodel import select
    from ..models.session_praat_result import SessionPraatResult
    from sqlalchemy import exc as sa_exc
    import logging
    
    # 기본 null 객체 정의
    empty_praat_result = SessionPraatResultResponse(
        avg_jitter_local=None,
        avg_shimmer_local=None,
        avg_hnr=None,
        avg_nhr=None,
        avg_lh_ratio_mean_db=None,
        avg_lh_ratio_sd_db=None,
        avg_max_f0=None,
        avg_min_f0=None,
        avg_intensity_mean=None,
        avg_f0=None,
        avg_f1=None,
        avg_f2=None,
        avg_cpp=None,
        avg_csid=None,
        created_at=None,
        updated_at=None
    )
    
    session_praat_result = empty_praat_result
    
    try:
        praat_stmt = select(SessionPraatResult).where(
            SessionPraatResult.training_session_id == session.id
        )
        praat_result = await db.execute(praat_stmt)
        praat_data = praat_result.scalar_one_or_none()
        
        if praat_data:
            session_praat_result = SessionPraatResultResponse(
                avg_jitter_local=praat_data.avg_jitter_local,
                avg_shimmer_local=praat_data.avg_shimmer_local,
                avg_hnr=praat_data.avg_hnr,
                avg_nhr=praat_data.avg_nhr,
                avg_lh_ratio_mean_db=praat_data.avg_lh_ratio_mean_db,
                avg_lh_ratio_sd_db=praat_data.avg_lh_ratio_sd_db,
                avg_max_f0=praat_data.avg_max_f0,
                avg_min_f0=praat_data.avg_min_f0,
                avg_intensity_mean=praat_data.avg_intensity_mean,
                avg_f0=praat_data.avg_f0,
                avg_f1=praat_data.avg_f1,
                avg_f2=praat_data.avg_f2,
                avg_cpp=praat_data.avg_cpp,
                avg_csid=praat_data.avg_csid,
                created_at=praat_data.created_at,
                updated_at=praat_data.updated_at
            )
    except (sa_exc.SQLAlchemyError, Exception) as e:
        # 🔥 모든 DB 예외를 캐치 (테이블 없음 / 컬럼 불일치 / 기타 전부)
        logging.warning(f"[convert_session_to_response] Session {session.id} Praat 조회 실패: {type(e).__name__} - {e}")
        # rollback 금지: 예외를 처리했으므로 세션은 유지됨
        try:
            await db.rollback()  # 혹시 트랜잭션이 열려있다면 여기서 수동 정리
        except Exception:
            pass  # rollback 실패해도 무시 (이미 예외 처리 중)
        session_praat_result = empty_praat_result
    
    # Composited media를 일괄 조회하기 위한 object_key 리스트 생성
    composited_object_keys = [
        f"results/{username}/{session.id}/result_item_{item.id}.mp4"
        for item in session.training_items
    ]
    
    # Composited media 일괄 조회
    media_service = MediaService(db)
    composited_media_map = {}
    if composited_object_keys:
        from ..models.media import MediaFile
        stmt = select(MediaFile).where(MediaFile.object_key.in_(composited_object_keys))
        result = await db.execute(stmt)
        composited_medias = result.scalars().all()
        composited_media_map = {media.object_key: media for media in composited_medias}
    
    # 🚀 성능 개선: Signed URL을 병렬로 생성
    # 1단계: URL 생성 작업 준비
    url_generation_tasks = []
    items_with_media = []  # (item, composited_media) 튜플 리스트
    
    for item in session.training_items:
        composited_object_key = f"results/{username}/{session.id}/result_item_{item.id}.mp4"
        composited_media = composited_media_map.get(composited_object_key)
        
        items_with_media.append((item, composited_media))
        
        # Composited media가 있으면 URL 생성 태스크 추가
        if composited_media:
            url_generation_tasks.append(
                gcs_service.get_signed_url(composited_media.object_key, expiration_hours=24)
            )
        else:
            # 없으면 None을 반환하는 더미 태스크 (순서 유지를 위해)
            url_generation_tasks.append(asyncio.sleep(0, result=None))
    
    # 2단계: 모든 URL을 병렬로 생성 (핵심 최적화!)
    # 예: 10개 아이템 → 순차: ~2초, 병렬: ~0.2초
    composited_video_urls = await asyncio.gather(*url_generation_tasks, return_exceptions=True)
    
    # 3단계: 결과 조립
    training_items = []
    for idx, (item, composited_media) in enumerate(items_with_media):
        # URL 생성 결과 가져오기 (예외 발생 시 None)
        composited_video_url = composited_video_urls[idx]
        if isinstance(composited_video_url, Exception):
            composited_video_url = None
        
        composited_media_file_id = composited_media.id if composited_media else None
        
        item_response = TrainingItemResponse(
            item_id=item.id,
            training_session_id=item.training_session_id,
            item_index=item.item_index,
            word_id=item.word_id,
            sentence_id=item.sentence_id,
            word=item.word.word if item.word else None,
            sentence=item.sentence.sentence if item.sentence else None,
            is_completed=item.is_completed,
            video_url=item.video_url,
            audio_url=item.audio_url,
            image_url=item.image_url,
            media_file_id=item.media_file_id,
            completed_at=item.completed_at,
            created_at=item.created_at,
            updated_at=item.updated_at,
            composited_video_url=composited_video_url,
            composited_media_file_id=composited_media_file_id
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
        session_praat_result=session_praat_result,
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


async def convert_praat_to_response(praat) -> Optional[PraatFeaturesResponse]:
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
        csid=praat.csid,
        lh_ratio_mean_db=praat.lh_ratio_mean_db,
        lh_ratio_sd_db=praat.lh_ratio_sd_db,
        f1=praat.f1,
        f2=praat.f2,
        intensity_mean=praat.intensity_mean
    )
