from fastapi import APIRouter, Depends, HTTPException, status, Query
from ..schemas import TrainSentenceCreate, TrainSentenceUpdate, TrainSentenceResponse
from ..schemas.common import NotFoundErrorResponse, ConflictErrorResponse
from ..services import SentenceService
from api.core.database import get_session
from api.modules.auth.services.service import get_current_admin_user
from api.modules.user.models.model import User
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(
    prefix="/sentences",
    tags=["sentences"],
)


async def get_service(db: AsyncSession = Depends(get_session)) -> SentenceService:
    return SentenceService(db)


@router.get(
    "",
    response_model=list[TrainSentenceResponse],
    summary="랜덤 문장 조회",
    description="데이터베이스에서 랜덤으로 문장을 조회합니다. limit 파라미터로 조회할 개수를 지정할 수 있습니다.",
    responses={
        200: {"description": "조회 성공"}
    }
)
async def get_random_sentences(
    limit: int = Query(1, description="조회할 문장 개수", ge=1, le=100),
    service: SentenceService = Depends(get_service)
):
    return await service.get_random_sentences(limit=limit)


@router.get(
    "/{sentence_id}",
    response_model=TrainSentenceResponse,
    summary="문장 상세 조회",
    description="특정 ID의 문장 상세 정보를 조회합니다.",
    responses={
        200: {"description": "조회 성공"},
        404: {"model": NotFoundErrorResponse, "description": "문장을 찾을 수 없음"}
    }
)
async def get_sentence_detail(
    sentence_id: int,
    service: SentenceService = Depends(get_service)
):
    sentence = await service.get_sentence_by_id(sentence_id)
    if not sentence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="문장을 찾을 수 없습니다."
        )
    return sentence


@router.post(
    "",
    response_model=TrainSentenceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="문장 생성",
    description="새로운 문장을 생성합니다. 문장은 4글자 이상 200글자 이하여야 하며, 공백만으로 이루어질 수 없습니다. (관리자 권한 필요)",
    responses={
        201: {"description": "생성 성공"},
        403: {"description": "관리자 권한이 필요합니다."},
        409: {"model": ConflictErrorResponse, "description": "문장 충돌 (중복 등)"}
    }
)
async def create_sentence(
    sentence_data: TrainSentenceCreate,
    service: SentenceService = Depends(get_service),
    current_admin: User = Depends(get_current_admin_user)
):
    try:
        return await service.create_sentence(sentence_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.put(
    "/{sentence_id}",
    response_model=TrainSentenceResponse,
    summary="문장 수정",
    description="기존 문장의 내용을 수정합니다. 문장은 4글자 이상 200글자 이하여야 하며, 공백만으로 이루어질 수 없습니다. (관리자 권한 필요)",
    responses={
        200: {"description": "수정 성공"},
        403: {"description": "관리자 권한이 필요합니다."},
        404: {"model": NotFoundErrorResponse, "description": "문장을 찾을 수 없음"},
        409: {"model": ConflictErrorResponse, "description": "문장 충돌 (중복 등)"}
    }
)
async def update_sentence(
    sentence_id: int,
    sentence_data: TrainSentenceUpdate,
    service: SentenceService = Depends(get_service),
    current_admin: User = Depends(get_current_admin_user)
):
    try:
        updated_sentence = await service.update_sentence(sentence_id, sentence_data)
        if not updated_sentence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="문장을 찾을 수 없습니다."
            )
        return updated_sentence
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.delete(
    "/{sentence_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="문장 삭제",
    description="지정된 ID의 문장을 삭제합니다. (관리자 권한 필요)",
    responses={
        204: {"description": "삭제 성공"},
        403: {"description": "관리자 권한이 필요합니다."},
        404: {"model": NotFoundErrorResponse, "description": "문장을 찾을 수 없음"}
    }
)
async def delete_sentence(
    sentence_id: int,
    service: SentenceService = Depends(get_service),
    current_admin: User = Depends(get_current_admin_user)
):
    deleted = await service.delete_sentence(sentence_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="문장을 찾을 수 없습니다."
        )
