from fastapi import APIRouter, Depends, HTTPException, status, Query
from ..schemas import TrainWordCreate, TrainWordUpdate, TrainWordResponse, DeleteSuccessResponse
from ..schemas.common import NotFoundErrorResponse, ConflictErrorResponse
from ..services import WordService
from api.core.database import get_session
from api.src.auth.auth_service import get_current_admin_user
from api.src.user.user_model import User
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(
    prefix="/words",
    tags=["words"],
)


async def get_service(db: AsyncSession = Depends(get_session)) -> WordService:
    return WordService(db)


@router.get(
    "",
    response_model=list[TrainWordResponse],
    summary="랜덤 단어 조회",
    description="데이터베이스에서 랜덤으로 단어를 조회합니다. limit 파라미터로 조회할 개수를 지정할 수 있습니다.",
    responses={
        200: {"description": "조회 성공"}
    }
)
async def get_random_words(
    limit: int = Query(1, description="조회할 단어 개수", ge=1, le=100),
    service: WordService = Depends(get_service)
):
    return await service.get_random_words(limit=limit)


@router.get(
    "/{word_id}",
    response_model=TrainWordResponse,
    summary="단어 상세 조회",
    description="특정 ID의 단어 상세 정보를 조회합니다.",
    responses={
        200: {"description": "조회 성공"},
        404: {"model": NotFoundErrorResponse, "description": "단어를 찾을 수 없음"}
    }
)
async def get_train_detail_word(
    word_id: int,
    service: WordService = Depends(get_service)
):
    word = await service.get_word_by_id(word_id)
    if not word:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="단어를 찾을 수 없습니다."
        )
    return word


@router.post(
    "",
    response_model=TrainWordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="단어 생성",
    description="새로운 단어를 생성합니다. 단어는 1글자 이상 20글자 이하여야 하며, 공백만으로 이루어질 수 없습니다. (관리자 권한 필요)",
    responses={
        201: {"description": "생성 성공"},
        403: {"description": "관리자 권한이 필요합니다."},
        409: {"model": ConflictErrorResponse, "description": "단어 충돌 (중복 등)"}
    }
)
async def create_train_word(
    train_word: TrainWordCreate,
    service: WordService = Depends(get_service),
    current_admin: User = Depends(get_current_admin_user)
):
    try:
        return await service.create_word(train_word)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.put(
    "/{word_id}",
    response_model=TrainWordResponse,
    summary="단어 수정",
    description="기존 단어의 내용을 수정합니다. 단어는 1글자 이상 20글자 이하여야 하며, 공백만으로 이루어질 수 없습니다. (관리자 권한 필요)",
    responses={
        200: {"description": "수정 성공"},
        403: {"description": "관리자 권한이 필요합니다."},
        404: {"model": NotFoundErrorResponse, "description": "단어를 찾을 수 없음"},
        409: {"model": ConflictErrorResponse, "description": "단어 충돌 (중복 등)"}
    }
)
async def update_train_word(
    word_id: int,
    train_word: TrainWordUpdate,
    service: WordService = Depends(get_service),
    current_admin: User = Depends(get_current_admin_user)
):
    try:
        updated_word = await service.update_word(word_id, train_word)
        if not updated_word:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="단어를 찾을 수 없습니다."
            )
        return updated_word
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.delete(
    "/{word_id}",
    response_model=DeleteSuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="단어 삭제",
    description="지정된 ID의 단어를 삭제합니다. (관리자 권한 필요)",
    responses={
        200: {"description": "삭제 성공"},
        403: {"description": "관리자 권한이 필요합니다."},
        404: {"model": NotFoundErrorResponse, "description": "단어를 찾을 수 없음"}
    }
)
async def delete_train_word(
    word_id: int,
    service: WordService = Depends(get_service),
    current_admin: User = Depends(get_current_admin_user)
):
    deleted = await service.delete_word(word_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="단어를 찾을 수 없습니다."
        )
    return DeleteSuccessResponse()
