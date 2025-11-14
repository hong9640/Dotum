from fastapi import Response, APIRouter, Depends, HTTPException, status, Query, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict
from datetime import date
import asyncio

from ..schemas.training_sessions import (
    TrainingSessionCreate,
    TrainingSessionResponse,
    TrainingSessionStatusUpdate,
    DailyTrainingResponse,
    ItemSubmissionResponse,
)
from ..schemas.training_items import CurrentItemResponse
from ..schemas.media import MediaUploadUrlResponse
from ..schemas.praat import (
    PraatFeaturesResponse, 
    VocalTrainingResultsSummary, 
    VocalTrainingResultsDetail
)
from ..schemas.common import NotFoundErrorResponse, BadRequestErrorResponse, UnauthorizedErrorResponse, ProcessingErrorResponse
from ..models.training_session import TrainingType, TrainingSessionStatus
from ..services.training_sessions import TrainingSessionService
from ..services.gcs import get_gcs_service, GCSService
from ..services.praat import get_praat_analysis_from_db
from ..services.batch_feedback import BatchFeedbackService
from ..services.response_converters import (
    convert_session_to_response,
    convert_media_to_response,
    convert_praat_to_response,
    build_current_item_response,
)
from api.core.database import get_session
from api.src.auth.auth_router import get_current_user
from api.src.user.user_model import User
from api.core.config import settings
from api.core.logging import get_logger

router = APIRouter(
    prefix="/training-sessions",
    tags=["training-sessions"],
)

logger = get_logger(__name__)


async def get_training_service(db: AsyncSession = Depends(get_session)) -> TrainingSessionService:
    return TrainingSessionService(db)


def provide_gcs_service() -> GCSService:
    """GCS 서비스 의존성"""
    return get_gcs_service(settings)


async def get_feedback_service(db: AsyncSession = Depends(get_session)) -> BatchFeedbackService:
    """배치 피드백 서비스 의존성"""
    return BatchFeedbackService(db)


async def _generate_feedback_in_background(session_id: int, user_name: str):
    """
    백그라운드 피드백 생성 (독립 DB 세션)
    
    BackgroundTasks는 응답 반환 후 실행되므로
    독립적인 DB 세션을 생성하여 사용해야 함
    """
    from api.core.database import async_session
    
    async with async_session() as db:
        try:
            logger.info(f"[Background] Starting feedback generation for session {session_id}")
            feedback_service = BatchFeedbackService(db)
            
            success = await feedback_service.generate_and_save_session_feedback(
                session_id=session_id,
                user_name=user_name
            )
            
            if success:
                logger.info(f"[Background] ✅ Feedback generation completed for session {session_id}")
            else:
                logger.warning(f"[Background] ⚠️ Feedback generation failed for session {session_id}")
                
        except Exception as e:
            logger.error(f"[Background] ❌ Error in feedback generation: {e}", exc_info=True)


@router.post(
    "",
    response_model=TrainingSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="훈련 세션 생성",
    description="새로운 훈련 세션을 생성합니다. 세션 이름, 훈련 타입, 아이템 개수 등을 지정할 수 있습니다.",
    responses={
        201: {"description": "훈련 세션 생성 성공"},
        400: {"model": BadRequestErrorResponse, "description": "잘못된 요청"},
        401: {"model": UnauthorizedErrorResponse, "description": "인증 필요"}
    }
)
async def create_training_session(
    session_data: TrainingSessionCreate,
    current_user: User = Depends(get_current_user),
    service: TrainingSessionService = Depends(get_training_service),
    gcs_service: GCSService = Depends(provide_gcs_service)
):
    """훈련 세션 생성"""
    try:
        new_session = await service.create_training_session(current_user.id, session_data)
        # 생성된 세션을 다시 조회하여 전체 정보 반환
        session = await service.get_training_session(new_session.id, current_user.id)
        if session:
            return await convert_session_to_response(session, service.db, gcs_service, current_user.username)
        return None
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "",
    response_model=List[TrainingSessionResponse],
    summary="사용자 훈련 세션 목록 조회",
    description="현재 사용자의 훈련 세션 목록을 조회합니다. 타입, 상태, 페이지네이션을 통해 필터링할 수 있습니다.",
    responses={
        200: {"description": "조회 성공"},
        401: {"model": UnauthorizedErrorResponse, "description": "인증 필요"}
    }
)
async def get_user_training_sessions(
    current_user: User = Depends(get_current_user),
    type: Optional[TrainingType] = Query(None, description="훈련 타입 필터"),
    status: Optional[TrainingSessionStatus] = Query(None, description="상태 필터"),
    limit: Optional[int] = Query(None, description="조회 개수 제한"),
    offset: int = Query(0, description="조회 시작 위치"),
    service: TrainingSessionService = Depends(get_training_service),
    gcs_service: GCSService = Depends(provide_gcs_service)
):
    """사용자의 훈련 세션 목록 조회 (병렬 변환 최적화)"""
    sessions = await service.get_user_training_sessions(
        user_id=current_user.id,
        type=type,
        status=status,
        limit=limit,
        offset=offset
    )
    
    # 🚀 성능 개선: 여러 세션을 병렬로 변환
    # 예: 10개 세션 → 순차: ~5초, 병렬: ~0.5초
    if not sessions:
        return []
    
    conversion_tasks = [
        convert_session_to_response(session, service.db, gcs_service, current_user.username)
        for session in sessions
    ]
    result = await asyncio.gather(*conversion_tasks)
    return result


@router.get(
    "/{session_id}",
    response_model=TrainingSessionResponse,
    summary="훈련 세션 상세 조회",
    description="특정 ID의 훈련 세션 상세 정보를 조회합니다. 세션의 진행 상황과 훈련 아이템 목록을 포함합니다.",
    responses={
        200: {"description": "조회 성공"},
        401: {"model": UnauthorizedErrorResponse, "description": "인증 필요"},
        404: {"model": NotFoundErrorResponse, "description": "세션을 찾을 수 없음"}
    }
)
async def get_training_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    service: TrainingSessionService = Depends(get_training_service),
    gcs_service: GCSService = Depends(provide_gcs_service)
):
    """특정 훈련 세션 조회"""
    session = await service.get_training_session(session_id, current_user.id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="훈련 세션을 찾을 수 없습니다."
        )
    return await convert_session_to_response(session, service.db, gcs_service, current_user.username)




@router.post(
    "/{session_id}/complete",
    response_model=TrainingSessionResponse,
    summary="훈련 세션 완료",
    description="진행 중인 훈련 세션을 완료 처리합니다. 모든 아이템이 완료되어야 세션을 완료할 수 있습니다.",
    responses={
        200: {"description": "완료 성공"},
        400: {"model": BadRequestErrorResponse, "description": "잘못된 요청"},
        401: {"model": UnauthorizedErrorResponse, "description": "인증 필요"},
        404: {"model": NotFoundErrorResponse, "description": "세션을 찾을 수 없음"}
    }
)
async def complete_training_session(
    session_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    service: TrainingSessionService = Depends(get_training_service),
    gcs_service: GCSService = Depends(provide_gcs_service)
):
    """훈련 세션 완료 (LLM 피드백은 백그라운드에서 생성)"""
    try:
        # 1. 세션 완료 처리 (즉시)
        session = await service.complete_training_session(session_id, current_user.id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="훈련 세션을 찾을 수 없습니다."
            )
        
        # 2. LLM 피드백 생성 (백그라운드 - 응답 후 처리)
        background_tasks.add_task(
            _generate_feedback_in_background,
            session_id=session.id,
            user_name=current_user.username
        )
        logger.info(f"[Complete] Session completed, feedback generation scheduled in background: session_id={session_id}")
        
        # 3. 즉시 응답 반환
        return await convert_session_to_response(session, service.db, gcs_service, current_user.username)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )




@router.patch(
    "/{session_id}/status",
    response_model=TrainingSessionResponse,
    summary="훈련 세션 상태 업데이트",
    description="훈련 세션의 상태를 업데이트합니다. 상태 전환 사유를 함께 제공할 수 있습니다.",
    responses={
        200: {"description": "업데이트 성공"},
        400: {"model": BadRequestErrorResponse, "description": "잘못된 요청"},
        401: {"model": UnauthorizedErrorResponse, "description": "인증 필요"},
        404: {"model": NotFoundErrorResponse, "description": "세션을 찾을 수 없음"}
    }
)
async def update_training_session_status(
    session_id: int,
    status_update: TrainingSessionStatusUpdate,
    current_user: User = Depends(get_current_user),
    service: TrainingSessionService = Depends(get_training_service),
    gcs_service: GCSService = Depends(provide_gcs_service)
):
    """훈련 세션 상태 업데이트 (유연한 상태 전환)"""
    try:
        session = await service.update_session_status(session_id, current_user.id, status_update)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="훈련 세션을 찾을 수 없습니다."
            )
        return await convert_session_to_response(session, service.db, gcs_service, current_user.username)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/calendar/{year}/{month}",
    response_model=Dict[str, int],
    summary="월별 훈련 달력 조회",
    description="지정된 연도와 월의 훈련 달력을 조회합니다. 날짜별 세션 수를 반환합니다.",
    responses={
        200: {"description": "조회 성공"},
        401: {"model": UnauthorizedErrorResponse, "description": "인증 필요"}
    }
)
async def get_training_calendar(
    year: int,
    month: int,
    type: Optional[TrainingType] = Query(None, description="훈련 타입 필터"),
    current_user: User = Depends(get_current_user),
    service: TrainingSessionService = Depends(get_training_service)
):
    """월별 훈련 달력 조회 (날짜별 세션 수)"""
    return await service.get_training_calendar(current_user.id, year, month, type)


@router.get(
    "/daily/{date_str}",
    response_model=DailyTrainingResponse,
    summary="일별 훈련 기록 조회",
    description="특정 날짜(YYYY-MM-DD 형식)의 훈련 기록을 조회합니다. 해당 날짜의 모든 세션 정보를 반환합니다.",
    responses={
        200: {"description": "조회 성공"},
        400: {"model": BadRequestErrorResponse, "description": "잘못된 날짜 형식"},
        401: {"model": UnauthorizedErrorResponse, "description": "인증 필요"}
    }
)
async def get_daily_training_records(
    date_str: str,
    type: Optional[TrainingType] = Query(None, description="훈련 타입 필터"),
    current_user: User = Depends(get_current_user),
    service: TrainingSessionService = Depends(get_training_service),
    gcs_service: GCSService = Depends(provide_gcs_service)
):
    """특정 날짜의 훈련 기록 조회 (병렬 변환 최적화)"""
    try:
        training_date = date.fromisoformat(date_str)
        sessions = await service.get_training_sessions_by_date(
            current_user.id, 
            training_date, 
            type
        )
        
        # 🚀 성능 개선: 여러 세션을 병렬로 변환
        if not sessions:
            converted_sessions = []
        else:
            conversion_tasks = [
                convert_session_to_response(session, service.db, gcs_service, current_user.username)
                for session in sessions
            ]
            converted_sessions = await asyncio.gather(*conversion_tasks)
        
        return DailyTrainingResponse(
            date=date_str, 
            sessions=converted_sessions,
            total_sessions=len(converted_sessions),
            completed_sessions=sum(1 for s in converted_sessions if s.status.value == 'completed'),
            in_progress_sessions=sum(1 for s in converted_sessions if s.status.value == 'in_progress')
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="잘못된 날짜 형식입니다. YYYY-MM-DD 형식으로 입력해주세요."
        )


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="훈련 세션 삭제",
    description="지정된 ID의 훈련 세션을 삭제합니다. 삭제된 세션은 복구할 수 없습니다.",
    responses={
        204: {"description": "삭제 성공"},
        401: {"model": UnauthorizedErrorResponse, "description": "인증 필요"},
        404: {"model": NotFoundErrorResponse, "description": "세션을 찾을 수 없음"}
    }
)
async def delete_training_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    service: TrainingSessionService = Depends(get_training_service)
):
    """훈련 세션 삭제"""
    deleted = await service.delete_training_session(session_id, current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="훈련 세션을 찾을 수 없습니다."
        )
    return


@router.post(
    "/{session_id}/retry",
    response_model=TrainingSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="완료된 훈련 세션 재훈련",
    description="완료된 훈련 세션을 똑같은 단어/문장으로 다시 훈련할 수 있는 새 세션을 생성합니다.",
    responses={
        201: {"description": "재훈련 세션 생성 성공"},
        400: {"model": BadRequestErrorResponse, "description": "완료되지 않은 세션이거나 잘못된 요청"},
        401: {"model": UnauthorizedErrorResponse, "description": "인증 필요"},
        404: {"model": NotFoundErrorResponse, "description": "세션을 찾을 수 없음"}
    }
)
async def retry_training_session(
    session_id: int,
    session_name: Optional[str] = Query(None, description="새 세션 이름 (지정하지 않으면 '기존이름 (재훈련)'으로 생성)"),
    current_user: User = Depends(get_current_user),
    service: TrainingSessionService = Depends(get_training_service),
    gcs_service: GCSService = Depends(provide_gcs_service)
):
    """완료된 훈련 세션을 똑같은 단어/문장으로 재훈련"""
    try:
        new_session = await service.retry_completed_session(
            session_id=session_id,
            user_id=current_user.id,
            session_name=session_name
        )
        # 생성된 세션을 다시 조회하여 전체 정보 반환
        session = await service.get_training_session(new_session.id, current_user.id)
        if session:
            return await convert_session_to_response(session, service.db, gcs_service, current_user.username)
        return None
    except LookupError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/{session_id}/current-item",
    response_model=CurrentItemResponse,
    summary="현재 진행 중인 아이템 조회",
    description="세션에서 현재 진행 중인 훈련 아이템을 조회합니다. 단어 또는 문장 정보와 다음 아이템 존재 여부를 반환합니다.",
    responses={
        200: {"description": "조회 성공"},
        401: {"model": UnauthorizedErrorResponse, "description": "인증 필요"},
        404: {"model": NotFoundErrorResponse, "description": "아이템을 찾을 수 없음"}
    }
)
async def get_current_item(
    session_id: int,
    current_user: User = Depends(get_current_user),
    service: TrainingSessionService = Depends(get_training_service),
    gcs_service: GCSService = Depends(provide_gcs_service)
):
    """현재 세션의 진행 중인 아이템 조회"""
    result = await service.get_current_item(session_id, current_user.id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="진행 중인 아이템을 찾을 수 없습니다."
        )
    
    # Composited media 미리 조회
    item = result['item']
    composited_object_key = f"results/{current_user.username}/{session_id}/result_item_{item.id}.mp4"
    from ..services.media import MediaService
    media_service = MediaService(service.db)
    composited_media = await media_service.get_media_file_by_object_key(composited_object_key)
    
    return await build_current_item_response(
        item=item,
        has_next=result['has_next'],
        praat=result.get('praat'),
        service=service,
        gcs_service=gcs_service,
        username=current_user.username,
        session_id=session_id,
        composited_media=composited_media
    )


@router.post(
    "/{session_id}/submit-current-item",
    response_model=ItemSubmissionResponse,
    summary="현재 진행중인 훈련 완료",
    description="현재 진행 중인 훈련 아이템에 동영상을 업로드하고 완료 처리합니다. 다음 훈련 아이템 정보도 함께 반환됩니다.",
    responses={
        200: {"description": "처리 성공"},
        400: {"model": BadRequestErrorResponse, "description": "잘못된 요청"},
        401: {"model": UnauthorizedErrorResponse, "description": "인증 필요"},
        404: {"model": NotFoundErrorResponse, "description": "세션 또는 아이템을 찾을 수 없음"}
    }
)
async def submit_current_item(
    session_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="제출할 동영상 파일"),
    current_user: User = Depends(get_current_user),
    service: TrainingSessionService = Depends(get_training_service),
    gcs_service: GCSService = Depends(provide_gcs_service)
):
    """현재 진행 중인 아이템에 동영상 업로드 및 완료 처리"""
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="동영상 파일만 업로드 가능합니다."
        )
    
    # 파일 크기 검증을 위해 먼저 읽기
    file_bytes = await file.read()
    max_size = 100 * 1024 * 1024  # 100MB
    if len(file_bytes) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="파일 크기는 100MB를 초과할 수 없습니다."
        )
    
    # 서비스 함수에는 스트리밍 처리를 위해 파일 포인터를 처음으로 되돌림
    await file.seek(0)
    
    try:
        result = await service.submit_current_item_with_video(
            session_id=session_id,
            user=current_user,
            video_file=file, # UploadFile 객체 자체를 전달
            filename=file.filename or "video.mp4",
            content_type=file.content_type or "video/mp4",
            gcs_service=gcs_service,
            background_tasks=background_tasks
        )
    except LookupError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    
    session = result["session"]
    next_item = result["next_item"]
    media_file = result["media_file"]
    praat_feature = result["praat_feature"]
    
    # 개별 아이템 피드백은 세션 완료시 배치로 생성 (즉시 피드백 불필요)
    
    next_item_response: Optional[CurrentItemResponse] = None
    if next_item:
        word = next_item.word.word if next_item.word else None
        sentence = next_item.sentence.sentence if next_item.sentence else None
        next_item_response = CurrentItemResponse(
            item_id=next_item.id,
            item_index=next_item.item_index,
            word_id=next_item.word_id,
            sentence_id=next_item.sentence_id,
            word=word,
            sentence=sentence,
            is_completed=next_item.is_completed,
            video_url=next_item.video_url,
            media_file_id=next_item.media_file_id,
            has_next=result.get("has_next", False)
        )
    
    return ItemSubmissionResponse(
        session=await convert_session_to_response(session, service.db, gcs_service, current_user.username),
        next_item=next_item_response,
        media=convert_media_to_response(media_file),
        praat=await convert_praat_to_response(praat_feature),
        video_url=result["video_url"]
    )


@router.post(
    "/{session_id}/vocal/{item_index}/submit",
    response_model=ItemSubmissionResponse,
    summary="발성 훈련 아이템 제출",
    description="발성 훈련 아이템에 오디오 파일과 그래프 이미지를 업로드하고 완료 처리합니다. Praat 분석을 수행하고 다음 아이템 정보도 함께 반환됩니다.",
    responses={
        200: {"description": "처리 성공"},
        400: {"model": BadRequestErrorResponse, "description": "잘못된 요청"},
        401: {"model": UnauthorizedErrorResponse, "description": "인증 필요"},
        404: {"model": NotFoundErrorResponse, "description": "세션 또는 아이템을 찾을 수 없음"}
    }
)
async def submit_vocal_item(
    session_id: int,
    item_index: int,
    audio_file: UploadFile = File(..., description="제출할 오디오 파일 (wav)"),
    graph_image: UploadFile = File(..., description="제출할 그래프 이미지 파일"),
    graph_video: Optional[UploadFile] = File(None, description="제출할 그래프 영상 파일 (선택사항)"),
    current_user: User = Depends(get_current_user),
    service: TrainingSessionService = Depends(get_training_service),
    gcs_service: GCSService = Depends(provide_gcs_service)
):
    """발성 훈련 아이템 제출 (오디오 + 그래프 이미지 업로드, 그래프 영상은 선택사항)"""
    # 파일 타입 검증
    if not audio_file.content_type or not audio_file.content_type.startswith("audio/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="오디오 파일만 업로드 가능합니다."
        )
    
    if not graph_image.content_type or not graph_image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미지 파일만 업로드 가능합니다."
        )
    
    # graph_video가 제공된 경우 타입 검증
    graph_video_bytes = None
    graph_video_filename = None
    graph_video_content_type = None
    if graph_video:
        if not graph_video.content_type or not graph_video.content_type.startswith("video/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="동영상 파일만 업로드 가능합니다."
            )
        graph_video_bytes = await graph_video.read()
        graph_video_filename = graph_video.filename or "graph.mp4"
        graph_video_content_type = graph_video.content_type or "video/mp4"
    
    # 파일 읽기
    audio_bytes = await audio_file.read()
    image_bytes = await graph_image.read()
    
    # 파일 크기 검증
    max_size = 100 * 1024 * 1024  # 100MB
    if len(audio_bytes) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="오디오 파일 크기는 100MB를 초과할 수 없습니다."
        )
    
    if len(image_bytes) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="이미지 파일 크기는 100MB를 초과할 수 없습니다."
        )
    
    if graph_video_bytes and len(graph_video_bytes) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="동영상 파일 크기는 100MB를 초과할 수 없습니다."
        )
    
    try:
        result = await service.submit_vocal_item(
            session_id=session_id,
            item_index=item_index,
            user=current_user,
            audio_file_bytes=audio_bytes,
            graph_image_bytes=image_bytes,
            audio_filename=audio_file.filename or "audio.wav",
            image_filename=graph_image.filename or "graph.png",
            audio_content_type=audio_file.content_type or "audio/wav",
            image_content_type=graph_image.content_type or "image/png",
            graph_video_bytes=graph_video_bytes,
            graph_video_filename=graph_video_filename,
            graph_video_content_type=graph_video_content_type,
            gcs_service=gcs_service
        )
    except LookupError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    
    session = result["session"]
    next_item = result["next_item"]
    media_file = result["media_file"]
    praat_feature = result["praat_feature"]
    video_url = result["video_url"]
    image_url = result.get("image_url")
    video_image_url = result.get("video_image_url")
    
    # 다음 아이템 응답 구성
    next_item_response: Optional[CurrentItemResponse] = None
    if next_item:
        # Composited media 미리 조회
        composited_object_key = f"results/{current_user.username}/{session_id}/result_item_{next_item.id}.mp4"
        from ..services.media import MediaService
        media_service = MediaService(service.db)
        composited_media = await media_service.get_media_file_by_object_key(composited_object_key)
        
        # 다음 아이템의 Praat 분석 결과는 아직 없을 가능성이 높으므로 None으로 설정
        # (VOCAL 타입의 경우 다음 아이템은 아직 완료되지 않았을 가능성이 높음)
        next_item_response = await build_current_item_response(
            item=next_item,
            has_next=result.get("has_next", False),
            praat=None,
            service=service,
            gcs_service=gcs_service,
            username=current_user.username,
            session_id=session_id,
            composited_media=composited_media
        )
    
    # STT 결과 변환 (있는 경우에만)
    from ..services.response_converters import convert_stt_to_response
    stt_response = await convert_stt_to_response(result.get("stt_result")) if result.get("stt_result") else None
    
    return ItemSubmissionResponse(
        session=await convert_session_to_response(session, service.db, gcs_service, current_user.username),
        next_item=next_item_response,
        media=convert_media_to_response(media_file),
        praat=await convert_praat_to_response(praat_feature),
        stt=stt_response,
        video_url=video_url,
        image_url=image_url,
        video_image_url=video_image_url
    )


@router.get(
    "/{session_id}/items/index/{item_index}",
    response_model=CurrentItemResponse,
    summary="item_index로 아이템 조회",
    description="특정 item_index의 아이템을 조회합니다. (세션 상태 무관)",
    responses={
        200: {"description": "조회 성공"},
        401: {"model": UnauthorizedErrorResponse, "description": "인증 필요"},
        404: {"model": NotFoundErrorResponse, "description": "아이템을 찾을 수 없음"}
    }
)
async def get_item_by_index(
    session_id: int,
    item_index: int,
    current_user: User = Depends(get_current_user),
    service: TrainingSessionService = Depends(get_training_service),
    gcs_service: GCSService = Depends(provide_gcs_service)
):
    """특정 인덱스 아이템 조회 (세션 상태 무관)"""
    result = await service.get_item_by_index(session_id, current_user.id, item_index)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 인덱스의 아이템을 찾을 수 없습니다."
        )

    # Composited media 미리 조회
    item = result['item']
    composited_object_key = f"results/{current_user.username}/{session_id}/result_item_{item.id}.mp4"
    from ..services.media import MediaService
    media_service = MediaService(service.db)
    composited_media = await media_service.get_media_file_by_object_key(composited_object_key)

    return await build_current_item_response(
        item=item,
        has_next=result['has_next'],
        praat=result.get('praat'),
        service=service,
        gcs_service=gcs_service,
        username=current_user.username,
        session_id=session_id,
        composited_media=composited_media
    )


@router.get(
    "/{session_id}/items/{item_id}/video",
    response_model=MediaUploadUrlResponse,
    summary="훈련 아이템 동영상 URL 발급",
    description="지정된 아이템의 동영상에 대한 서명 URL을 생성해 반환합니다.",
    responses={
        200: {"description": "URL 발급 성공"},
        401: {"model": UnauthorizedErrorResponse, "description": "인증 필요"},
        404: {"model": NotFoundErrorResponse, "description": "세션 또는 아이템을 찾을 수 없음"}
    }
)
async def get_item_video_url(
    session_id: int,
    item_id: int,
    current_user: User = Depends(get_current_user),
    service: TrainingSessionService = Depends(get_training_service),
    gcs_service: GCSService = Depends(provide_gcs_service)
):
    """아이템 동영상의 서명 URL 발급"""
    result = await service.get_item_with_media(session_id=session_id, item_id=item_id, user_id=current_user.id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="훈련 아이템을 찾을 수 없습니다.")
    item = result["item"]
    media = result["media"]
    if not media or not media.object_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="해당 아이템의 동영상을 찾을 수 없습니다.")
    signed_url = await gcs_service.get_signed_url(media.object_key, expiration_hours=24)
    if not signed_url:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="서명 URL 생성에 실패했습니다.")
    return MediaUploadUrlResponse(upload_url=signed_url, media_file_id=media.id, expires_in=24*3600)

## Removed legacy complete endpoint in favor of submit endpoint


@router.put(
    "/{session_id}/items/{item_id}/video",
    response_model=ItemSubmissionResponse,
    summary="훈련 아이템 동영상 재업로드(교체)",
    description="완료된 아이템을 포함하여 특정 아이템의 동영상을 재업로드합니다. 진행률 변경 없이 기존 영상을 교체합니다.",
    responses={
        200: {"description": "재업로드 성공"},
        400: {"model": BadRequestErrorResponse, "description": "잘못된 요청"},
        401: {"model": UnauthorizedErrorResponse, "description": "인증 필요"},
        404: {"model": NotFoundErrorResponse, "description": "세션 또는 아이템을 찾을 수 없음"}
    }
)
async def resubmit_item_video(
    session_id: int,
    item_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="재업로드할 동영상 파일"),
    current_user: User = Depends(get_current_user),
    service: TrainingSessionService = Depends(get_training_service),
    gcs_service: GCSService = Depends(provide_gcs_service)
):
    """특정 훈련 아이템의 동영상을 재업로드(교체)"""
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="동영상 파일만 업로드 가능합니다."
        )

    # 파일 크기 검증을 위해 먼저 읽기
    file_bytes = await file.read()
    max_size = 100 * 1024 * 1024  # 100MB
    if len(file_bytes) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="파일 크기는 100MB를 초과할 수 없습니다."
        )
    # 서비스 함수에는 스트리밍 처리를 위해 파일 포인터를 처음으로 되돌림
    await file.seek(0)

    try:
        result = await service.resubmit_item_video(
            session_id=session_id,
            item_id=item_id,
            user=current_user,
            video_file=file, # UploadFile 객체 자체를 전달
            filename=file.filename or "video.mp4",
            content_type=file.content_type or "video/mp4",
            gcs_service=gcs_service,
            background_tasks=background_tasks
        )
    except LookupError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

    return ItemSubmissionResponse(
        session=await convert_session_to_response(result["session"], service.db, gcs_service, current_user.username),
        next_item=None,
        media=convert_media_to_response(result["media_file"]),
        praat=await convert_praat_to_response(result["praat_feature"]),
        video_url=result["video_url"],
        message="동영상이 교체되었습니다."
    )

@router.get(
    "/{session_id}/items/{item_id}/result",
    response_model=MediaUploadUrlResponse,
    summary="Wav2Lip 결과 영상 URL 조회",
    description="훈련 아이템에 대한 Wav2Lip 처리 결과 영상의 서명된 URL을 조회합니다.",
    responses={
        200: {"description": "URL 조회 성공"},
        202: {"model": ProcessingErrorResponse, "description": "영상 처리 중"},
        401: {"model": UnauthorizedErrorResponse, "description": "인증 필요"},
        404: {"model": NotFoundErrorResponse, "description": "세션, 아이템 또는 결과 영상을 찾을 수 없음"}
    }
)
async def get_wav2lip_result_video(
    session_id: int,
    item_id: int,
    current_user: User = Depends(get_current_user),
    service: TrainingSessionService = Depends(get_training_service),
    gcs_service: GCSService = Depends(provide_gcs_service)
):
    """Wav2Lip 결과 영상 URL 조회"""
    try:
        result = await service.get_wav2lip_result(
            session_id=session_id,
            item_id=item_id,
            user=current_user,
            gcs_service=gcs_service
        )
        if result is None:
            # 결과가 없으면 처리 중으로 간주
            return Response(status_code=status.HTTP_202_ACCEPTED, content="Video is still processing.")
        
        return MediaUploadUrlResponse(
            upload_url=result["signed_url"],
            media_file_id=result["media_file"].id,
            expires_in=3600  # 1시간 (초 단위)
        )

    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    

@router.get(
    "/{session_id}/items/{item_id}/praat",
    response_model=PraatFeaturesResponse,
    status_code=status.HTTP_200_OK,
    summary="praat 데이터 가져오기",
    responses={
        403: {"description": "Forbidden (Not owner)"},
        404: {"description": "Media file not found"},
    }
)
async def read_praat_analysis(
    session_id: int,
    item_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    특정 미디어 파일의 Praat 분석 결과를 조회합니다.
    - (200 OK): 분석 완료
    - (404 Not Found): 원본 미디어 파일 없음
    - (403 Forbidden): 파일 소유자가 아님
    """
    try:
        analysis_results = await get_praat_analysis_from_db(
            session_id=session_id,
            item_id=item_id,
            db=db,
            user_id=current_user.id
        )
        
        if analysis_results:
            return analysis_results
        else:
            # 분석 결과가 없으면 404 처리
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Praat analysis not found.")

    except LookupError as e:
        # 원본 미디어 파일이 없음
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        # 파일 소유자가 아님
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get(
    "/{session_id}/vocal-results",
    response_model=VocalTrainingResultsSummary,
    summary="VOCAL 훈련 결과 요약 조회 (평균)",
    description="VOCAL 타입 훈련 세션의 평균 Praat 지표를 반환합니다. 세션이 완료되면 저장된 평균값을 반환하고, 진행 중이면 실시간 계산 결과를 반환합니다.",
    responses={
        200: {"description": "조회 성공"},
        400: {"model": BadRequestErrorResponse, "description": "VOCAL 타입이 아님 또는 데이터 부족"},
        401: {"model": UnauthorizedErrorResponse, "description": "인증 필요"},
        404: {"model": NotFoundErrorResponse, "description": "세션을 찾을 수 없음"}
    }
)
async def get_vocal_training_results_summary(
    session_id: int,
    current_user: User = Depends(get_current_user),
    service: TrainingSessionService = Depends(get_training_service)
):
    """VOCAL 타입 훈련 세션의 평균 Praat 결과 조회
    
    - 완료된 세션: DB에 저장된 평균 결과 반환
    - 진행 중인 세션: 현재까지 제출된 아이템으로 실시간 평균 계산
    """
    try:
        # 1. 세션 조회 및 권한 확인
        session = await service.get_training_session(session_id, current_user.id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="훈련 세션을 찾을 수 없습니다."
            )
        
        # 2. VOCAL 타입 확인
        if session.type != TrainingType.VOCAL:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이 API는 VOCAL 타입 세션에서만 사용할 수 있습니다."
            )
        
        # 3. 완료된 세션이면 DB에 저장된 평균 결과 조회
        if session.status == TrainingSessionStatus.COMPLETED:
            db_result = await service.session_praat_repo.get_by_session_id(session_id)
            if db_result:
                return VocalTrainingResultsSummary(
                    session_id=session.id,
                    session_name=session.session_name,
                    total_items=session.total_items,
                    completed_items=session.completed_items,
                    average_results=db_result
                )
        
        # 4. 진행 중이거나 DB에 저장된 결과가 없으면 실시간 계산
        result = await service.get_vocal_results_summary(session_id, current_user.id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="훈련 세션을 찾을 수 없습니다."
            )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/{session_id}/vocal-results/detail",
    response_model=VocalTrainingResultsDetail,
    summary="VOCAL 훈련 결과 상세 조회 (아이템별)",
    description="VOCAL 타입 훈련 세션의 각 아이템별 Praat 분석 결과를 모두 반환합니다.",
    responses={
        200: {"description": "조회 성공"},
        400: {"model": BadRequestErrorResponse, "description": "VOCAL 타입이 아님"},
        401: {"model": UnauthorizedErrorResponse, "description": "인증 필요"},
        404: {"model": NotFoundErrorResponse, "description": "세션을 찾을 수 없음"}
    }
)
async def get_vocal_training_results_detail(
    session_id: int,
    current_user: User = Depends(get_current_user),
    service: TrainingSessionService = Depends(get_training_service)
):
    """VOCAL 타입 훈련 세션의 아이템별 상세 Praat 결과 조회"""
    try:
        result = await service.get_vocal_results_detail(session_id, current_user.id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="훈련 세션을 찾을 수 없습니다."
            )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )