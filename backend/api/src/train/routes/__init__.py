from fastapi import APIRouter
from .words import router as words_router
from .sentences import router as sentences_router
from .results import word_results_router, sentence_results_router

# 모든 train 관련 router를 통합
router = APIRouter()
router.include_router(words_router)
router.include_router(sentences_router)
router.include_router(word_results_router)
router.include_router(sentence_results_router)

__all__ = ["router"]

