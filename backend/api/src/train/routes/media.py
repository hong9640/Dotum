"""
미디어 파일 관련 API 라우터
동영상 업로드/다운로드/관리 엔드포인트
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime
import io

from api.core.database import get_session
from api.core.config import settings
from api.src.train.services.gcs_service import get_gcs_service, GCSService
from api.src.auth.auth_service import get_current_user
from api.src.user.user_model import User
from api.src.train.models.media import MediaFile, MediaType, MediaStatus
from ..schemas.media import (
    MediaResponse, 
    MediaListResponse, 
    MediaUploadUrlResponse,
    MediaFilter
)
from ..services.media import MediaService

router = APIRouter(
    prefix="/media",
    tags=["media"]
)


# 공통 헬퍼 함수
async def get_media_file_with_permission_check(
    media_id: int,
    current_user: User,
    db: AsyncSession
) -> MediaFile:
    """미디어 파일 조회 및 권한 확인"""
    media_service = MediaService(db)
    media_file = await media_service.get_media_file_by_id(media_id)
    
    if not media_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="동영상 파일을 찾을 수 없습니다."
        )
    
    if media_file.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="다른 사용자의 파일에 접근할 수 없습니다."
        )
    
    return media_file


@router.post(
    "/upload/video",
    response_model=MediaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="동영상 파일 업로드",
    description="훈련 세션과 연동된 동영상을 GCS에 업로드하고 데이터베이스에 메타데이터를 저장합니다."
)
async def upload_video(
    file: UploadFile = File(..., description="업로드할 동영상 파일"),
    session_id: str = Query(..., description="훈련 세션 ID"),
    train_id: Optional[int] = Query(None, description="훈련 ID (단어 훈련용)"),
    result_id: Optional[int] = Query(None, description="결과 ID (문장 훈련용)"),
    word_id: Optional[int] = Query(None, description="단어 ID"),
    sentence_id: Optional[int] = Query(None, description="문장 ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """동영상 파일 업로드"""
    
    # 파일 타입 검증
    if not file.content_type or not file.content_type.startswith('video/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="동영상 파일만 업로드 가능합니다."
        )
    
    # 파일 크기 제한 (100MB)
    max_size = 100 * 1024 * 1024  # 100MB
    if file.size and file.size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="파일 크기는 100MB를 초과할 수 없습니다."
        )
    
    # 파라미터 검증
    if not ((train_id is not None and word_id is not None) or (result_id is not None and sentence_id is not None)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="train_id+word_id 또는 result_id+sentence_id가 필요합니다."
        )
    
    try:
        # 파일 내용 읽기
        file_content = await file.read()
        
        # GCS 서비스 초기화
        gcs_service = get_gcs_service(settings)
        
        # GCS에 파일 업로드
        upload_result = await gcs_service.upload_video(
            file_content=file_content,
            username=current_user.username,
            session_id=session_id,
            train_id=train_id,
            result_id=result_id,
            word_id=word_id,
            sentence_id=sentence_id,
            original_filename=file.filename,
            content_type=file.content_type
        )
        
        if not upload_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"파일 업로드 실패: {upload_result['error']}"
            )
        
        # 데이터베이스에 메타데이터 저장
        media_service = MediaService(db)
        media_file = await media_service.create_media_file(
            user_id=current_user.id,
            object_key=upload_result["object_path"],
            media_type=MediaType.VIDEO,
            file_name=upload_result["filename"],
            file_size_bytes=upload_result["file_size"],
            format=file.content_type.split('/')[-1],
            is_public=False
        )
        
        return MediaResponse(
            id=media_file.id,
            user_id=media_file.user_id,
            object_key=media_file.object_key,
            media_type=media_file.media_type,
            file_name=media_file.file_name,
            file_size_bytes=media_file.file_size_bytes,
            format=media_file.format,
            duration_ms=media_file.duration_ms,
            width_px=media_file.width_px,
            height_px=media_file.height_px,
            status=media_file.status,
            is_public=media_file.is_public,
            created_at=media_file.created_at,
            updated_at=media_file.updated_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"동영상 업로드 중 오류가 발생했습니다: {str(e)}"
        )


@router.get(
    "/videos",
    response_model=List[MediaListResponse],
    status_code=status.HTTP_200_OK,
    summary="사용자 동영상 목록 조회",
    description="현재 로그인한 사용자의 동영상 파일 목록을 조회합니다. JWT 토큰에서 사용자 정보를 자동으로 추출합니다."
)
async def get_user_videos(
    media_type: Optional[MediaType] = None,
    status: Optional[MediaStatus] = None,
    current_user: User = Depends(get_current_user),  # JWT 토큰에서 자동으로 현재 사용자 추출
    db: AsyncSession = Depends(get_session)
):
    """
    사용자 동영상 목록 조회
    
    설명:
    - Authorization 헤더에 Bearer 토큰을 포함해야 합니다
    - JWT 토큰에서 사용자 정보를 자동으로 추출합니다
    - 현재 로그인한 사용자의 동영상만 조회 가능합니다
    """
    
    try:
        media_service = MediaService(db)
        videos = await media_service.get_user_media_files(
            user_id=current_user.id,  # JWT 토큰에서 추출한 사용자 ID 사용
            media_type=media_type,
            status=status
        )
        
        return [
            MediaListResponse(
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
                created_at=video.created_at
            )
            for video in videos
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"동영상 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get(
    "/session/{session_id}/videos",
    response_model=List[MediaListResponse],
    status_code=status.HTTP_200_OK,
    summary="세션별 동영상 목록 조회",
    description="특정 훈련 세션의 동영상 파일 목록을 조회합니다."
)
async def get_session_videos(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """세션별 동영상 목록 조회"""
    
    try:
        # GCS에서 세션별 동영상 목록 조회
        gcs_service = get_gcs_service(settings)
        videos = await gcs_service.list_user_videos(
            username=current_user.username,
            session_filter=session_id
        )
        
        # 데이터베이스에서 메타데이터 조회
        media_service = MediaService(db)
        media_files = []
        
        for video_info in videos:
            # object_key로 미디어 파일 조회
            media_file = await media_service.get_media_file_by_object_key(video_info["object_path"])
            if media_file and media_file.user_id == current_user.id:
                media_files.append(MediaListResponse(
                    id=media_file.id,
                    object_key=media_file.object_key,
                    media_type=media_file.media_type,
                    file_name=media_file.file_name,
                    file_size_bytes=media_file.file_size_bytes,
                    format=media_file.format,
                    duration_ms=media_file.duration_ms,
                    width_px=media_file.width_px,
                    height_px=media_file.height_px,
                    status=media_file.status,
                    is_public=media_file.is_public,
                    created_at=media_file.created_at
                ))
        
        return media_files
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"세션 동영상 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )


# 이유: 서버를 통한 릴레이 방식은 비효율적입니다 (GCS → 서버 → 클라이언트)
# 대신 /signed-url/{media_id} 엔드포인트를 사용하여 클라이언트가 직접 GCS에서 다운로드하세요.


@router.delete(
    "/{media_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="동영상 파일 삭제",
    description="지정된 동영상 파일을 삭제합니다."
)
async def delete_video(
    media_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """동영상 파일 삭제"""
    
    try:
        # 미디어 파일 조회 및 권한 확인
        media_file = await get_media_file_with_permission_check(media_id, current_user, db)
        
        # GCS에서 파일 삭제
        gcs_service = get_gcs_service(settings)
        delete_success = await gcs_service.delete_video(media_file.object_key)
        
        if not delete_success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="파일 삭제에 실패했습니다."
            )
        
        # 데이터베이스에서도 삭제
        media_service = MediaService(db)
        await media_service.delete_media_file(media_id)
        
        return {"message": "동영상 파일이 성공적으로 삭제되었습니다."}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"파일 삭제 중 오류가 발생했습니다: {str(e)}"
        )


@router.get(
    "/signed-url/{media_id}",
    response_model=MediaUploadUrlResponse,
    status_code=status.HTTP_200_OK,
    summary="동영상 임시 접근 URL 생성 (다운로드 및 시청)",
    description="동영상 파일에 대한 임시 접근 URL을 생성합니다. 이 URL을 사용하여 다운로드이거나 시청할 수 있습니다."
)
async def get_signed_url(
    media_id: int,
    expiration_hours: int = 1,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    try:
        # 미디어 파일 조회 및 권한 확인
        media_file = await get_media_file_with_permission_check(media_id, current_user, db)
        
        # 서명된 URL 생성
        gcs_service = get_gcs_service(settings)
        signed_url = await gcs_service.get_signed_url(
            media_file.object_key, 
            expiration_hours
        )
        
        if not signed_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="임시 URL 생성에 실패했습니다."
            )
        
        return MediaUploadUrlResponse(
            upload_url=signed_url,
            media_file_id=media_file.id,
            expires_in=expiration_hours * 3600
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"임시 URL 생성 중 오류가 발생했습니다: {str(e)}"
        )
