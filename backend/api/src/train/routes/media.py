"""
미디어 파일 관련 API 라우터 - 사용자 동영상 목록 조회만 제공
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response, Security
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from api.core.database import get_session
from api.core.config import settings
from api.src.train.services.gcs_service import get_gcs_service
from api.src.auth.auth_router import get_current_user
from api.src.user.user_model import User
from ..services.media import MediaService
from ..schemas.media import MediaListResponse
from api.src.train.services.praat import get_praat_analysis_from_db
from api.src.train.schemas.praat import PraatFeaturesResponse


router = APIRouter(
    prefix="/media",
    tags=["media"],
)

@router.get(
    "/videos",
    response_model=List[MediaListResponse],
    status_code=status.HTTP_200_OK,
    summary="사용자 동영상 목록 조회",
    description="현재 로그인한 사용자의 동영상 파일 목록을 조회합니다. 각 항목에 24시간 유효한 서명 URL이 포함됩니다."
)
async def get_user_videos(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    try:
        media_service = MediaService(db)
        videos = await media_service.get_user_media_files(user_id=current_user.id)
        gcs_service = get_gcs_service(settings)
        result: List[MediaListResponse] = []
        for video in videos:
            signed_url = await gcs_service.get_signed_url(video.object_key, expiration_hours=24)
            result.append(MediaListResponse(
                id=video.id,
                object_key=video.object_key,
                media_type=video.media_type,
                file_name=video.file_name,
                file_size_bytes=video.file_size_bytes,
                format=video.format,
                duration_ms=video.duration_ms,
                width_px=video.width_px,
                height_px=video.height_px,
                status=video.status,
                is_public=video.is_public,
                created_at=video.created_at,
                signed_url=signed_url
            ))
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"동영상 목록 조회 중 오류: {str(e)}"
        )

@router.get(
    "/{media_id}/praat",
    response_model=PraatFeaturesResponse,
    status_code=status.HTTP_200_OK,
    responses={
        202: {"description": "Analysis is still processing"},
        403: {"description": "Forbidden (Not owner)"},
        404: {"description": "Media file not found"},
    }
)
async def read_praat_analysis(
    media_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    특정 미디어 파일의 Praat 분석 결과를 조회합니다.
    - (200 OK): 분석 완료
    - (202 Accepted): 분석 처리 중
    - (404 Not Found): 원본 미디어 파일 없음
    - (403 Forbidden): 파일 소유자가 아님
    """
    try:
        analysis_results = await get_praat_analysis_from_db(
            db=db,
            media_id=media_id + 1,
            user_id=current_user.id
        )
        
        if analysis_results:
            return analysis_results
        else:
            # Case 2: 분석 처리 중
            # 202 코드를 반환하기 위해 Response 객체를 사용
            return Response(status_code=status.HTTP_202_ACCEPTED)

    except LookupError as e:
        # Case 3: 원본 미디어 파일이 없음
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        # Case 4: 파일 소유자가 아님
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
