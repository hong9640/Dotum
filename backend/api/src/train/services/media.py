from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlmodel import SQLModel

from api.src.train.models.media import MediaFile, MediaType, MediaStatus
from api.src.train.schemas.media import MediaCreate, MediaUpdate


class MediaService:
    """미디어 파일 서비스"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_media_file(
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
        is_public: bool = False
    ) -> MediaFile:
        """미디어 파일 생성"""
        
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
            status=MediaStatus.UPLOADED
        )
        
        self.db.add(media_file)
        await self.db.commit()
        await self.db.refresh(media_file)
        
        return media_file
    
    async def get_media_file_by_id(self, media_id: int) -> Optional[MediaFile]:
        """ID로 미디어 파일 조회"""
        
        result = await self.db.execute(
            select(MediaFile).where(MediaFile.id == media_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_media_files(
        self,
        user_id: int,
        media_type: Optional[MediaType] = None,
        status: Optional[MediaStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[MediaFile]:
        """사용자의 미디어 파일 목록 조회"""
        
        query = select(MediaFile).where(MediaFile.user_id == user_id)
        
        if media_type:
            query = query.where(MediaFile.media_type == media_type)
        
        if status:
            query = query.where(MediaFile.status == status)
        
        query = query.order_by(MediaFile.created_at.desc()).limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def update_media_file(
        self, 
        media_id: int, 
        update_data: MediaUpdate
    ) -> Optional[MediaFile]:
        """미디어 파일 정보 업데이트"""
        
        media_file = await self.get_media_file_by_id(media_id)
        if not media_file:
            return None
        
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(media_file, field, value)
        
        await self.db.commit()
        await self.db.refresh(media_file)
        
        return media_file
    
    async def delete_media_file(self, media_id: int) -> bool:
        """미디어 파일 삭제"""
        
        media_file = await self.get_media_file_by_id(media_id)
        if not media_file:
            return False
        
        await self.db.delete(media_file)
        await self.db.commit()
        
        return True
    
    async def get_media_files_by_date_range(
        self,
        user_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        media_type: Optional[MediaType] = None
    ) -> List[MediaFile]:
        """날짜 범위로 미디어 파일 조회"""
        
        query = select(MediaFile).where(MediaFile.user_id == user_id)
        
        if start_date:
            query = query.where(MediaFile.created_at >= start_date)
        
        if end_date:
            query = query.where(MediaFile.created_at <= end_date)
        
        if media_type:
            query = query.where(MediaFile.media_type == media_type)
        
        query = query.order_by(MediaFile.created_at.desc())
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_media_file_by_object_key(self, object_key: str) -> Optional[MediaFile]:
        """객체 키로 미디어 파일 조회"""
        
        result = await self.db.execute(
            select(MediaFile).where(MediaFile.object_key == object_key)
        )
        return result.scalar_one_or_none()
    
    async def update_media_status(
        self, 
        media_id: int, 
        status: MediaStatus
    ) -> Optional[MediaFile]:
        """미디어 파일 상태 업데이트"""
        
        media_file = await self.get_media_file_by_id(media_id)
        if not media_file:
            return None
        
        media_file.status = status
        await self.db.commit()
        await self.db.refresh(media_file)
        
        return media_file