from fastapi import APIRouter
from .words import router as words_router
from .sentences import router as sentences_router
from .training_sessions import router as training_sessions_router
from .media import router as media_router

# 모든 train 관련 router를 통합
router = APIRouter()
# 통합 훈련 세션 API
router.include_router(training_sessions_router)
# 기본 데이터 관리 API들
router.include_router(words_router)
router.include_router(sentences_router)
# 미디어 파일 API
router.include_router(media_router)

__all__ = ["router"]

