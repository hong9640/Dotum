from fastapi import APIRouter
from .words import router as words_router

# 모든 train 관련 router를 통합
router = APIRouter()
router.include_router(words_router)

__all__ = ["router"]

