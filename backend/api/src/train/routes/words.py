from fastapi import APIRouter, Depends, HTTPException, status
from ..schemas import TrainWordCreate, TrainWordUpdate, TrainWordResponse
from ..services import WordService
from api.core.database import get_session
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(
    prefix="/words",
    tags=["words"],
)


async def get_service(db: AsyncSession = Depends(get_session)) -> WordService:
    return WordService(db)


@router.get("", response_model=list[TrainWordResponse])
async def get_random_words(
    limit: int = 1,
    service: WordService = Depends(get_service)
):
    return await service.get_random_words(limit=limit)


@router.get("/{word_id}", response_model=TrainWordResponse)
async def get_train_detail_word(
    word_id: int,
    service: WordService = Depends(get_service)
):
    word = await service.get_word_by_id(word_id)
    if not word:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Word not found"
        )
    return word


@router.post("", response_model=TrainWordResponse, status_code=status.HTTP_201_CREATED)
async def create_train_word(
    train_word: TrainWordCreate,
    service: WordService = Depends(get_service)
):
    try:
        return await service.create_word(train_word)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.put("/{word_id}", response_model=TrainWordResponse)
async def update_train_word(
    word_id: int,
    train_word: TrainWordUpdate,
    service: WordService = Depends(get_service)
):
    try:
        updated_word = await service.update_word(word_id, train_word)
        if not updated_word:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Word not found"
            )
        return updated_word
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.delete("/{word_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_train_word(
    word_id: int,
    service: WordService = Depends(get_service)
):
    deleted = await service.delete_word(word_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Word not found"
        )
