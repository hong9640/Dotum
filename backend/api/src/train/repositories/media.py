"""
Media Repository
미디어 파일 관련 DB 작업을 처리하는 Repository
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from ..models.media import MediaFile, MediaType, MediaStatus
from .base import BaseRepository


class MediaRepository(BaseRepository[MediaFile]):
    """미디어 파일 Repository"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, MediaFile)
    
    async def create_and_flush(
        self,
        user_id: int,
        object_key: str,
        media_type: MediaType,
        file_name: str,
        file_size_bytes: int,
        format: str,
        duration_ms: Optional[int] = None,
        width_px: Optional[int] = None,
        height_px: Optional[int] = None,
        is_public: bool = False,
        status: MediaStatus = MediaStatus.UPLOADED
    ) -> MediaFile:
        """미디어 파일 생성 (flush만 수행, commit은 호출자가 담당)"""
        media_file = MediaFile(
            user_id=user_id,
            object_key=object_key,
            media_type=media_type,
            file_name=file_name,
            file_size_bytes=file_size_bytes,
            format=format,
            duration_ms=duration_ms,
            width_px=width_px,
            height_px=height_px,
            is_public=is_public,
            status=status
        )
        
        self.db.add(media_file)
        await self.db.flush()  # commit 없이 flush만
        return media_file
    
    async def update_media_file(
        self,
        media_file: MediaFile,
        file_name: Optional[str] = None,
        file_size_bytes: Optional[int] = None,
        format: Optional[str] = None,
        status: Optional[MediaStatus] = None
    ) -> MediaFile:
        """미디어 파일 정보 업데이트 (flush만 수행)"""
        if file_name is not None:
            media_file.file_name = file_name
        if file_size_bytes is not None:
            media_file.file_size_bytes = file_size_bytes
        if format is not None:
            media_file.format = format
        if status is not None:
            media_file.status = status
        
        media_file.updated_at = datetime.now()
        await self.db.flush()
        return media_file

