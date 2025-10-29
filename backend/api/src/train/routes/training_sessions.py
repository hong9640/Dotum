from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict
from datetime import date

from ..schemas.training_sessions import (
    TrainingSessionCreate,
    TrainingSessionResponse,
    TrainingSessionStatusUpdate,
    DailyTrainingResponse,
    ItemSubmissionResponse,
)
from ..schemas.training_items import CurrentItemResponse
from ..schemas.common import NotFoundErrorResponse, BadRequestErrorResponse, UnauthorizedErrorResponse
from ..services.training_sessions import TrainingSessionService
from ..models.training_session import TrainingType, TrainingSessionStatus
from api.core.database import get_session
from api.src.auth.auth_router import get_current_user
from api.src.user.user_model import User
from api.core.config import settings
from api.src.train.services.gcs_service import get_gcs_service, GCSService
from ..schemas.media import MediaUploadUrlResponse


router = APIRouter(
    prefix="/training-sessions",
    tags=["training-sessions"],
)


async def get_training_service(db: AsyncSession = Depends(get_session)) -> TrainingSessionService:
    return TrainingSessionService(db)


def provide_gcs_service() -> GCSService:
    """GCS 서비스 의존성"""
    return get_gcs_service(settings)


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
    service: TrainingSessionService = Depends(get_training_service)
):
    """훈련 세션 생성"""
    try:
        new_session = await service.create_training_session(current_user.id, session_data)
        # 생성된 세션을 다시 조회하여 전체 정보 반환
        return await service.get_training_session(new_session.id, current_user.id)
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
    service: TrainingSessionService = Depends(get_training_service)
):
    """사용자의 훈련 세션 목록 조회"""
    sessions = await service.get_user_training_sessions(
        user_id=current_user.id,
        type=type,
        status=status,
        limit=limit,
        offset=offset
    )
    return sessions


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
    service: TrainingSessionService = Depends(get_training_service)
):
    """특정 훈련 세션 조회"""
    session = await service.get_training_session(session_id, current_user.id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="훈련 세션을 찾을 수 없습니다."
        )
    return session




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
    current_user: User = Depends(get_current_user),
    service: TrainingSessionService = Depends(get_training_service)
):
    """훈련 세션 완료"""
    try:
        session = await service.complete_training_session(session_id, current_user.id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="훈련 세션을 찾을 수 없습니다."
            )
        return session
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
    service: TrainingSessionService = Depends(get_training_service)
):
    """훈련 세션 상태 업데이트 (유연한 상태 전환)"""
    try:
        session = await service.update_session_status(session_id, current_user.id, status_update)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="훈련 세션을 찾을 수 없습니다."
            )
        return session
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
    service: TrainingSessionService = Depends(get_training_service)
):
    """특정 날짜의 훈련 기록 조회"""
    try:
        training_date = date.fromisoformat(date_str)
        sessions = await service.get_training_sessions_by_date(
            current_user.id, 
            training_date, 
            type
        )
        return DailyTrainingResponse(date=date_str, sessions=sessions)
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
    
    item = result['item']
    has_next = result['has_next']
    
    # 단어 또는 문장 정보 추출
    word = item.word.word if item.word else None
    sentence = item.sentence.sentence if item.sentence else None
    
    # Private 버킷이므로 signed URL 생성
    video_url = None
    if item.video_url and item.media_file_id:
        # 기존 동영상이 있으면 signed URL 생성
        media_file = await service.get_media_file_by_id(item.media_file_id)
        if media_file:
            video_url = await gcs_service.get_signed_url(media_file.object_key, expiration_hours=24)
    
    return CurrentItemResponse(
        id=item.id,
        item_index=item.item_index,
        word_id=item.word_id,
        sentence_id=item.sentence_id,
        word=word,
        sentence=sentence,
        is_completed=item.is_completed,
        video_url=video_url,
        media_file_id=item.media_file_id,
        has_next=has_next
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
    
    file_bytes = await file.read()
    max_size = 100 * 1024 * 1024  # 100MB
    if len(file_bytes) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="파일 크기는 100MB를 초과할 수 없습니다."
        )
    
    try:
        result = await service.submit_current_item_with_video(
            session_id=session_id,
            user=current_user,
            file_bytes=file_bytes,
            filename=file.filename or "video.mp4",
            content_type=file.content_type or "video/mp4",
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
    
    next_item_response: Optional[CurrentItemResponse] = None
    if next_item:
        word = next_item.word.word if next_item.word else None
        sentence = next_item.sentence.sentence if next_item.sentence else None
        next_item_response = CurrentItemResponse(
            id=next_item.id,
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
        session=session,
        next_item=next_item_response,
        media=media_file,
        video_url=result["video_url"]
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
