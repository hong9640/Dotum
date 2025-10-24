from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict
from datetime import date

from ..schemas.training_sessions import (
    TrainingSessionCreate,
    TrainingSessionUpdate,
    TrainingSessionResponse,
    TrainingSessionStatusUpdate,
    CalendarResponse,
    DailyTrainingResponse,
    CreateSuccessResponse
)
from ..services.training_sessions import TrainingSessionService
from ..models.training_session import TrainingType, TrainingSessionStatus
from api.core.database import get_session
from api.src.auth.auth_router import get_current_user
from api.src.user.user_model import User


router = APIRouter(
    prefix="/training-sessions",
    tags=["training-sessions"],
)


async def get_training_service(db: AsyncSession = Depends(get_session)) -> TrainingSessionService:
    return TrainingSessionService(db)


@router.post("", response_model=CreateSuccessResponse, status_code=status.HTTP_201_CREATED)
async def create_training_session(
    session_data: TrainingSessionCreate,
    current_user: User = Depends(get_current_user),
    service: TrainingSessionService = Depends(get_training_service)
):
    """훈련 세션 생성"""
    try:
        new_session = await service.create_training_session(current_user.id, session_data)
        return CreateSuccessResponse(session_id=new_session.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("", response_model=List[TrainingSessionResponse])
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


@router.get("/{session_id}", response_model=TrainingSessionResponse)
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




@router.post("/{session_id}/complete", response_model=TrainingSessionResponse)
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




@router.patch("/{session_id}/status", response_model=TrainingSessionResponse)
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


@router.get("/calendar/{year}/{month}", response_model=Dict[str, int])
async def get_training_calendar(
    year: int,
    month: int,
    type: Optional[TrainingType] = Query(None, description="훈련 타입 필터"),
    current_user: User = Depends(get_current_user),
    service: TrainingSessionService = Depends(get_training_service)
):
    """월별 훈련 달력 조회 (날짜별 세션 수)"""
    return await service.get_training_calendar(current_user.id, year, month, type)


@router.get("/daily/{date_str}", response_model=DailyTrainingResponse)
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


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
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