from fastapi import APIRouter, Depends, HTTPException, status
from ..schemas import TrainSentenceCreate, TrainSentenceUpdate, TrainSentenceResponse
from ..services import SentenceService
from api.core.database import get_session
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(
    prefix="/sentences",
    tags=["sentences"],
)


async def get_service(db: AsyncSession = Depends(get_session)) -> SentenceService:
    return SentenceService(db)


@router.get("", response_model=list[TrainSentenceResponse])
async def get_random_sentences(
    limit: int = 1,
    service: SentenceService = Depends(get_service)
):
    return await service.get_random_sentences(limit=limit)


@router.get("/{sentence_id}", response_model=TrainSentenceResponse)
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


@router.post("", response_model=TrainSentenceResponse, status_code=status.HTTP_201_CREATED)
async def create_sentence(
    sentence_data: TrainSentenceCreate,
    service: SentenceService = Depends(get_service)
):
    try:
        return await service.create_sentence(sentence_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.put("/{sentence_id}", response_model=TrainSentenceResponse)
async def update_sentence(
    sentence_id: int,
    sentence_data: TrainSentenceUpdate,
    service: SentenceService = Depends(get_service)
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


@router.delete("/{sentence_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sentence(
    sentence_id: int,
    service: SentenceService = Depends(get_service)
):
    deleted = await service.delete_sentence(sentence_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="문장을 찾을 수 없습니다."
        )
