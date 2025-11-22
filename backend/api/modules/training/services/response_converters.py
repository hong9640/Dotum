"""
Response converters for training session endpoints.
DB 모델을 API Response 스키마로 변환하는 헬퍼 함수들
"""
import asyncio
from typing import Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.training_sessions import (
    TrainingSessionResponse,
    TrainingSessionSummaryResponse,
)
from ..schemas.training_items import CurrentItemResponse, TrainingItemResponse
from ..schemas.media import MediaResponse
from ..schemas.praat import PraatFeaturesResponse, SessionPraatResultResponse
from ..schemas.stt import SttResultResponse
from ..services.training_sessions import TrainingSessionService
from ..services.gcs import GCSService
from ..services.media import MediaService
from api.shared.utils.file_utils import build_graph_image_candidate_keys

# Sentinel value: "조회하지 않음"을 나타내기 위한 특별한 객체
_NOT_PROVIDED = object()


async def _generate_graph_image_signed_url(
    item,
    username: str,
    session_id: int,
    gcs_service: GCSService,
    expiration_hours: int = 24
) -> Optional[str]:
    """저장된 image_url을 기반으로 VOCAL 그래프 이미지를 재서명"""
    if not item or item.item_index is None:
        return None

    # 이미지가 없는 세션 타입이면 건너뜀
    if not item.image_url:
        return None

    candidate_keys = build_graph_image_candidate_keys(
        username=username,
        session_id=session_id,
        item_index=item.item_index,
        stored_image_url=item.image_url
    )

    tried: set[str] = set()
    for object_key in candidate_keys:
        if not object_key or object_key in tried:
            continue
        tried.add(object_key)
        signed_url = await gcs_service.get_signed_url(object_key, expiration_hours=expiration_hours)
        if signed_url:
            return signed_url
    return None


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

    refreshed_image_url = await _generate_graph_image_signed_url(
        item=item,
        username=username,
        session_id=session_id,
        gcs_service=gcs_service
    )
    if refreshed_image_url:
        item.image_url = refreshed_image_url

    # Item feedback 및 세부 피드백 조회
    feedback_obj = None
    
    try:
        from sqlmodel import select
        from ..models.training_item_praat_feedback import TrainItemPraatFeedback
        from ..models.praat import PraatFeatures
        from ..models.media import MediaFile
        from ..schemas.training_items import FeedbackResponse
        
        # 아이템의 audio media 찾기
        if item.media_file_id:
            video_media = item.media_file
            if video_media and video_media.object_key and video_media.object_key.endswith('.mp4'):
                audio_key = video_media.object_key.replace('.mp4', '.wav').replace('.MP4', '.wav')
                audio_media_stmt = select(MediaFile).where(MediaFile.object_key == audio_key)
                audio_result = await service.db.execute(audio_media_stmt)
                audio_media = audio_result.scalar_one_or_none()
                if audio_media:
                    praat_stmt = select(PraatFeatures).where(PraatFeatures.media_id == audio_media.id)
                    praat_result = await service.db.execute(praat_stmt)
                    praat_feature = praat_result.scalar_one_or_none()
                    if praat_feature:
                        feedback_stmt = select(TrainItemPraatFeedback).where(
                            TrainItemPraatFeedback.praat_features_id == praat_feature.id
                        ).order_by(TrainItemPraatFeedback.created_at.desc())
                        feedback_result = await service.db.execute(feedback_stmt)
                        feedback = feedback_result.scalar_one_or_none()
                        if feedback:
                            # 피드백 객체 생성 (프론트엔드에서 키로 접근 가능)
                            feedback_obj = FeedbackResponse(
                                item=feedback.item_feedback,
                                vowel_distortion=feedback.vowel_distortion_feedback,
                                sound_stability=feedback.sound_stability_feedback,
                                voice_clarity=feedback.voice_clarity_feedback,
                                voice_health=feedback.voice_health_feedback
                            )
    except Exception as e:
        import logging
        logging.warning(f"[build_current_item_response] Item {item.id} feedback 조회 실패: {type(e).__name__} - {e}")

    return CurrentItemResponse(
        item_id=item.id,
        item_index=item.item_index,
        word_id=item.word_id,
        sentence_id=item.sentence_id,
        word=word,
        sentence=sentence,
        is_completed=item.is_completed,
        feedback=feedback_obj,  # 피드백 객체
        video_url=video_url,
        composited_video_url=composited_video_url,
        media_file_id=item.media_file_id,
        composited_media_file_id=composited_media_file_id,
        has_next=has_next,
        praat=(await convert_praat_to_response(praat, item=item) if praat else None),
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

    refreshed_image_url = await _generate_graph_image_signed_url(
        item=item,
        username=username,
        session_id=session_id,
        gcs_service=gcs_service
    )
    if refreshed_image_url:
        item.image_url = refreshed_image_url
    
    # Item feedback 조회
    item_feedback = None
    try:
        from sqlmodel import select
        from ..models.training_item_praat_feedback import TrainItemPraatFeedback
        from ..models.praat import PraatFeatures
        from ..models.media import MediaFile
        
        # 아이템의 audio media 찾기
        if item.media_file_id:
            video_media = item.media_file
            if video_media and video_media.object_key and video_media.object_key.endswith('.mp4'):
                audio_key = video_media.object_key.replace('.mp4', '.wav').replace('.MP4', '.wav')
                audio_media_stmt = select(MediaFile).where(MediaFile.object_key == audio_key)
                audio_result = await db.execute(audio_media_stmt)
                audio_media = audio_result.scalar_one_or_none()
                if audio_media:
                    praat_stmt = select(PraatFeatures).where(PraatFeatures.media_id == audio_media.id)
                    praat_result = await db.execute(praat_stmt)
                    praat = praat_result.scalar_one_or_none()
                    if praat:
                        feedback_stmt = select(TrainItemPraatFeedback).where(
                            TrainItemPraatFeedback.praat_features_id == praat.id
                        ).order_by(TrainItemPraatFeedback.created_at.desc())
                        feedback_result = await db.execute(feedback_stmt)
                        feedback = feedback_result.scalar_one_or_none()
                        if feedback:
                            item_feedback = feedback.item_feedback
    except Exception as e:
        import logging
        logging.warning(f"[convert_training_item_to_response] Item {item.id} feedback 조회 실패: {type(e).__name__} - {e}")
    
    return TrainingItemResponse(
        item_id=item.id,
        training_session_id=item.training_session_id,
        item_index=item.item_index,
        word_id=item.word_id,
        sentence_id=item.sentence_id,
        word=item.word.word if item.word else None,
        sentence=item.sentence.sentence if item.sentence else None,
        is_completed=item.is_completed,
        feedback=item_feedback,  # 피드백 추가
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
    username: str,
    include_media_urls: bool = True,
    include_training_items: bool = True,
    include_praat_summary: bool = True,
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
    overall_feedback = None  # 세션 피드백
    
    if include_praat_summary:
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
                
                # 세션 피드백 조회
                try:
                    from ..models.training_session_praat_feedback import TrainSessionPraatFeedback
                    feedback_stmt = select(TrainSessionPraatFeedback).where(
                        TrainSessionPraatFeedback.session_praat_result_id == praat_data.id
                    ).order_by(TrainSessionPraatFeedback.created_at.desc())
                    feedback_result = await db.execute(feedback_stmt)
                    session_feedback = feedback_result.scalar_one_or_none()
                    if session_feedback:
                        overall_feedback = session_feedback.feedback_text
                except Exception as e:
                    logging.warning(f"[convert_session_to_response] Session {session.id} Feedback 조회 실패: {type(e).__name__} - {e}")
                    
        except (sa_exc.SQLAlchemyError, Exception) as e:
            # 🔥 모든 DB 예외를 캐치 (테이블 없음 / 컬럼 불일치 / 기타 전부)
            logging.warning(f"[convert_session_to_response] Session {session.id} Praat 조회 실패: {type(e).__name__} - {e}")
            # rollback 금지
            try:
                await db.rollback()
            except Exception:
                pass
            session_praat_result = empty_praat_result
    
    training_items: list[TrainingItemResponse] = []
    if include_training_items:
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
        
        # 🚀 성능 개선: Signed URL을 배치로 생성
        items_with_media = []  # (item, composited_media) 튜플 리스트
        for item in session.training_items:
            composited_object_key = f"results/{username}/{session.id}/result_item_{item.id}.mp4"
            composited_media = composited_media_map.get(composited_object_key)
            items_with_media.append((item, composited_media))
        
        signed_composited_urls: Dict[str, Optional[str]] = {}
        if include_media_urls:
            composited_keys = [
                composited_media.object_key
                for _, composited_media in items_with_media
                if composited_media
            ]
            if composited_keys:
                signed_composited_urls = await gcs_service.get_signed_urls_batch(
                    composited_keys,
                    expiration_hours=24
                )
        
        # 3단계: 결과 조립
        # Item feedback 일괄 조회 (N+1 문제 해결)
        item_feedback_map = {}
        try:
            from ..models.training_item_praat_feedback import TrainItemPraatFeedback
            from ..models.praat import PraatFeatures
            from ..models.media import MediaFile

            # 3-1. 아이템별 audio media object_key 준비
            audio_key_by_item: dict[int, str] = {}
            for item, _ in items_with_media:
                video_media = item.media_file
                if (
                    item.media_file_id 
                    and video_media 
                    and video_media.object_key 
                    and video_media.object_key.endswith(('.mp4', '.MP4'))
                ):
                    audio_key = video_media.object_key.replace('.mp4', '.wav').replace('.MP4', '.wav')
                    audio_key_by_item[item.id] = audio_key
            
            # 3-2. Audio media + Praat + Feedback을 한 번의 JOIN으로 조회
            if audio_key_by_item:
                audio_keys = list(set(audio_key_by_item.values()))
                audio_stmt = (
                    select(
                        MediaFile.object_key,
                        TrainItemPraatFeedback.item_feedback
                    )
                    .join(PraatFeatures, PraatFeatures.media_id == MediaFile.id)
                    .outerjoin(
                        TrainItemPraatFeedback,
                        TrainItemPraatFeedback.praat_features_id == PraatFeatures.id
                    )
                    .where(MediaFile.object_key.in_(audio_keys))
                    .order_by(TrainItemPraatFeedback.created_at.desc())
                )
                audio_result = await db.execute(audio_stmt)
                audio_rows = audio_result.all()
                
                # object_key -> item_id 매핑
                item_id_by_audio_key = {audio_key: item_id for item_id, audio_key in audio_key_by_item.items()}
                
                for audio_object_key, feedback_text in audio_rows:
                    item_id = item_id_by_audio_key.get(audio_object_key)
                    if (
                        item_id is not None
                        and feedback_text
                        and item_id not in item_feedback_map
                    ):
                        item_feedback_map[item_id] = feedback_text
        except Exception as e:
            logging.warning(f"[convert_session_to_response] Item feedback 조회 실패: {type(e).__name__} - {e}")
        
        for item, composited_media in items_with_media:
            # URL 생성 결과 가져오기
            composited_video_url = None
            if include_media_urls and composited_media:
                composited_video_url = signed_composited_urls.get(composited_media.object_key)
            
            composited_media_file_id = composited_media.id if composited_media else None
            
            # Item feedback 가져오기
            item_feedback = item_feedback_map.get(item.id)
            
            refreshed_image_url = None
            if include_media_urls:
                refreshed_image_url = await _generate_graph_image_signed_url(
                    item=item,
                    username=username,
                    session_id=session.id,
                    gcs_service=gcs_service
                )
                if refreshed_image_url:
                    item.image_url = refreshed_image_url

            item_response = TrainingItemResponse(
                item_id=item.id,
                training_session_id=item.training_session_id,
                item_index=item.item_index,
                word_id=item.word_id,
                sentence_id=item.sentence_id,
                word=item.word.word if item.word else None,
                sentence=item.sentence.sentence if item.sentence else None,
                is_completed=item.is_completed,
                feedback=item_feedback,  # 피드백 추가
                video_url=item.video_url if include_media_urls else None,
                audio_url=item.audio_url if include_media_urls else None,
                image_url=item.image_url if include_media_urls else None,
                media_file_id=item.media_file_id,
                completed_at=item.completed_at,
                created_at=item.created_at,
                updated_at=item.updated_at,
                composited_video_url=composited_video_url,
                composited_media_file_id=composited_media_file_id
            )
            training_items.append(item_response)
    
    # 실제 training_items 관계에서 아이템 개수와 완료된 아이템 개수 계산
    # training_items가 로드되어 있으면 실제 데이터를 사용, 없으면 세션 필드 값 사용
    if hasattr(session, 'training_items') and session.training_items is not None:
        actual_total_items = len(session.training_items)
        actual_completed_items = sum(1 for item in session.training_items if item.is_completed)
    else:
        # training_items가 로드되지 않은 경우 세션 필드 값 사용
        actual_total_items = session.total_items
        actual_completed_items = session.completed_items
    
    return TrainingSessionResponse(
        session_id=session.id,
        user_id=session.user_id,
        session_name=session.session_name,
        type=session.type,
        status=session.status,
        training_date=session.training_date,
        total_items=actual_total_items,
        completed_items=actual_completed_items,
        current_item_index=session.current_item_index,
        progress_percentage=session.progress_percentage,
        overall_feedback=overall_feedback,  # 세션 피드백 추가
        session_praat_result=session_praat_result if include_praat_summary else empty_praat_result,
        session_metadata=session.session_metadata,
        created_at=session.created_at,
        updated_at=session.updated_at,
        started_at=session.started_at,
        completed_at=session.completed_at,
        training_items=training_items
    )


def convert_session_to_summary_response(session) -> TrainingSessionSummaryResponse:
    """경량 세션 요약 응답 생성"""
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

    # 실제 training_items 관계에서 아이템 개수와 완료된 아이템 개수 계산
    # training_items가 로드되어 있으면 실제 데이터를 사용, 없으면 세션 필드 값 사용
    if hasattr(session, 'training_items') and session.training_items is not None:
        actual_total_items = len(session.training_items)
        actual_completed_items = sum(1 for item in session.training_items if item.is_completed)
    else:
        # training_items가 로드되지 않은 경우 세션 필드 값 사용
        actual_total_items = session.total_items
        actual_completed_items = session.completed_items

    return TrainingSessionSummaryResponse(
        session_id=session.id,
        user_id=session.user_id,
        session_name=session.session_name,
        type=session.type,
        status=session.status,
        training_date=session.training_date,
        total_items=actual_total_items,
        completed_items=actual_completed_items,
        current_item_index=session.current_item_index,
        progress_percentage=session.progress_percentage,
        average_score=session.average_score,
        overall_feedback=session.overall_feedback,
        session_praat_result=empty_praat_result,
        session_metadata=session.session_metadata,
        created_at=session.created_at,
        updated_at=session.updated_at,
        started_at=session.started_at,
        completed_at=session.completed_at,
        training_items=[]
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


async def convert_praat_to_response(
    praat, 
    item=None
) -> Optional[PraatFeaturesResponse]:
    """PraatFeatures 모델을 PraatFeaturesResponse로 변환
    
    Args:
        praat: PraatFeatures 모델 객체
        item: TrainingItem 모델 객체 (image_url 추가용)
    """
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
        intensity_mean=praat.intensity_mean,
        image_url=item.image_url if item else None
    )


async def convert_stt_to_response(
    stt_result
) -> Optional[SttResultResponse]:
    """TrainingItemSttResults 모델을 SttResultResponse로 변환
    
    Args:
        stt_result: TrainingItemSttResults 모델 객체
    """
    if stt_result is None:
        return None
    
    return SttResultResponse(
        id=stt_result.id,
        training_item_id=stt_result.training_item_id,
        ai_model_id=stt_result.ai_model_id,
        stt_result=stt_result.stt_result,
        created_at=stt_result.created_at
    )
