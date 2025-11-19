"""
UserRepository - 사용자 데이터 접근 계층
"""
from typing import Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from pydantic import EmailStr

from api.shared.repositories.base import BaseRepository
from ..models.model import User


class UserRepository(BaseRepository[User]):
    """사용자 Repository"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, User)
    
    async def get_by_email(self, email: Union[str, EmailStr], include_deleted: bool = False) -> Optional[User]:
        """
        이메일로 사용자 조회
        
        Args:
            email: 조회할 이메일
            include_deleted: True면 삭제된 사용자도 포함, False면 삭제되지 않은 사용자만 조회
        """
        # EmailStr는 타입 힌트일 뿐, 실제로는 문자열로 처리
        email_str = str(email)
        stmt = select(User).where(User.username == email_str)
        
        # 삭제되지 않은 사용자만 조회 (기본값)
        if not include_deleted:
            stmt = stmt.where(User.deleted_at.is_(None))
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def exists_by_email(self, email: Union[str, EmailStr], include_deleted: bool = False) -> bool:
        """
        이메일 존재 여부 확인
        
        Args:
            email: 확인할 이메일
            include_deleted: True면 삭제된 사용자도 포함, False면 삭제되지 않은 사용자만 확인
        """
        user = await self.get_by_email(email, include_deleted=include_deleted)
        return user is not None
    
    async def soft_delete(self, user: User) -> User:
        """사용자 소프트 삭제 (deleted_at 설정)"""
        from datetime import datetime
        user.deleted_at = datetime.now()
        return await self.update(user)

