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
from ..services.training_sessions import TrainingSessionService, get_training_service
from ..repositories.training_items import TrainingItemRepository 
from api.src.train.services.gcs_service import get_gcs_service, GCSService

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
                media_id=video.id,
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
    summary="praat 데이터 가져오기(임시)",
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

@router.get(
    "/results/{item_id}",
    summary="wav2lip 결과 영상 URL 조회",
    description="훈련 아이템 ID를 기반으로 wav2lip 처리 결과 영상의 Signed URL을 조회합니다.",
    responses={
        200: {"description": "URL 조회 성공"},
        202: {"description": "영상 처리 중"},
        404: {"description": "아이템 또는 결과 영상을 찾을 수 없음"}
    }
)
async def get_wav2lip_result_video(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
    gcs_service: GCSService = Depends(get_gcs_service)
):
    # 1. item_id로 TrainingItem 정보를 가져옵니다.

    item_repo = TrainingItemRepository(db)

    output_object_key = f"results/{current_user.username}/some_session_id/result_word_some_word_id.mp4" # 실제로는 DB에서 가져와야 함

    # 3. GCS에서 파일 존재 여부 확인
    blob = gcs_service.bucket.blob(output_object_key)
    if not blob.exists():
        # 파일이 없으면 처리 중이므로 202 Accepted 반환
        return Response(status_code=status.HTTP_202_ACCEPTED, content="Video is still processing.")

    # 4. 파일이 있으면 Signed URL 생성 후 반환
    signed_url = await gcs_service.get_signed_url(output_object_key, expiration_hours=1)
    if not signed_url:
        raise HTTPException(status_code=500, detail="URL 생성에 실패했습니다.")
        
    return {"video_url": signed_url}