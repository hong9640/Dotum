"""
AI Model Repository
AI 모델 버전 관련 DB 작업을 처리하는 Repository
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.ai_model import AIModel
from api.shared.repositories.base import BaseRepository


class AIModelRepository(BaseRepository[AIModel]):
    """AI 모델 Repository"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, AIModel)
    
    async def get_by_version(self, version: str) -> Optional[AIModel]:
        """버전으로 AI 모델 조회"""
        stmt = select(AIModel).where(AIModel.version == version)
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def get_or_create(self, version: str) -> AIModel:
        """버전으로 AI 모델 조회 또는 생성"""
        model = await self.get_by_version(version)
        if model:
            return model
        
        # 새로운 모델 생성
        model = AIModel(version=version)
        self.db.add(model)
        await self.db.flush()
        return model

