from fastapi import APIRouter, Depends, HTTPException, status
from ..schemas import (
    WordTrainResultCreate,
    WordTrainResultUpdate,
    WordTrainResultResponse,
    SentenceTrainResultCreate,
    SentenceTrainResultUpdate,
    SentenceTrainResultResponse,
)
from ..services import WordTrainResultService, SentenceTrainResultService
from api.core.database import get_session
from sqlalchemy.ext.asyncio import AsyncSession

# Word Train Results Router
word_results_router = APIRouter(
    prefix="/word-results",
    tags=["word-results"],
)


async def get_word_service(db: AsyncSession = Depends(get_session)) -> WordTrainResultService:
    return WordTrainResultService(db)


@word_results_router.get("", response_model=list[WordTrainResultResponse])
async def get_word_results_by_user(
    user_id: int,
    limit: int = 100,
    service: WordTrainResultService = Depends(get_word_service)
):
    return await service.get_results_by_user(user_id, limit)


@word_results_router.get("/{result_id}", response_model=WordTrainResultResponse)
async def get_word_result_detail(
    result_id: int,
    service: WordTrainResultService = Depends(get_word_service)
):
    result = await service.get_result_by_id(result_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="단어 훈련 결과를 찾을 수 없습니다."
        )
    return result


@word_results_router.post("", response_model=WordTrainResultResponse, status_code=status.HTTP_201_CREATED)
async def create_word_result(
    result_data: WordTrainResultCreate,
    service: WordTrainResultService = Depends(get_word_service)
):
    return await service.create_result(result_data)


@word_results_router.put("/{result_id}", response_model=WordTrainResultResponse)
async def update_word_result(
    result_id: int,
    result_data: WordTrainResultUpdate,
    service: WordTrainResultService = Depends(get_word_service)
):
    updated_result = await service.update_result(result_id, result_data)
    if not updated_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="단어 훈련 결과를 찾을 수 없습니다."
        )
    return updated_result


@word_results_router.delete("/{result_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_word_result(
    result_id: int,
    service: WordTrainResultService = Depends(get_word_service)
):
    deleted = await service.delete_result(result_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="단어 훈련 결과를 찾을 수 없습니다."
        )


# Sentence Train Results Router
sentence_results_router = APIRouter(
    prefix="/sentence-results",
    tags=["sentence-results"],
)


async def get_sentence_service(db: AsyncSession = Depends(get_session)) -> SentenceTrainResultService:
    return SentenceTrainResultService(db)


@sentence_results_router.get("", response_model=list[SentenceTrainResultResponse])
async def get_sentence_results_by_user(
    user_id: int,
    limit: int = 100,
    service: SentenceTrainResultService = Depends(get_sentence_service)
):
    return await service.get_results_by_user(user_id, limit)


@sentence_results_router.get("/{result_id}", response_model=SentenceTrainResultResponse)
async def get_sentence_result_detail(
    result_id: int,
    service: SentenceTrainResultService = Depends(get_sentence_service)
):
    result = await service.get_result_by_id(result_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="문장 훈련 결과를 찾을 수 없습니다."
        )
    return result


@sentence_results_router.post("", response_model=SentenceTrainResultResponse, status_code=status.HTTP_201_CREATED)
async def create_sentence_result(
    result_data: SentenceTrainResultCreate,
    service: SentenceTrainResultService = Depends(get_sentence_service)
):
    return await service.create_result(result_data)


@sentence_results_router.put("/{result_id}", response_model=SentenceTrainResultResponse)
async def update_sentence_result(
    result_id: int,
    result_data: SentenceTrainResultUpdate,
    service: SentenceTrainResultService = Depends(get_sentence_service)
):
    updated_result = await service.update_result(result_id, result_data)
    if not updated_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="문장 훈련 결과를 찾을 수 없습니다."
        )
    return updated_result


@sentence_results_router.delete("/{result_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sentence_result(
    result_id: int,
    service: SentenceTrainResultService = Depends(get_sentence_service)
):
    deleted = await service.delete_result(result_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="문장 훈련 결과를 찾을 수 없습니다."
        )

