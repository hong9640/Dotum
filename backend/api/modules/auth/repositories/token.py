"""
RefreshTokenRepository - 리프레시 토큰 데이터 접근 계층
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, delete

from api.shared.repositories.base import BaseRepository
from ..models.token import RefreshToken


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    """리프레시 토큰 Repository"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, RefreshToken)
    
    async def get_by_hash(self, token_hash: str) -> Optional[RefreshToken]:
        """토큰 해시로 조회"""
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def delete_by_hash_and_user_id(
        self, 
        token_hash: str, 
        user_id: int
    ) -> bool:
        """토큰 해시와 사용자 ID로 삭제"""
        stmt = delete(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.user_id == user_id
        )
        result = await self.db.execute(stmt)
        await self.db.commit()  # 실제 서비스에서는 commit 필요
        return result.rowcount > 0
    
    async def delete_by_id(self, token_id: int) -> bool:
        """토큰 ID로 삭제"""
        stmt = delete(RefreshToken).where(RefreshToken.id == token_id)
        result = await self.db.execute(stmt)
        await self.db.commit()  # 실제 서비스에서는 commit 필요
        return result.rowcount > 0

