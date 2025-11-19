"""
Praat Repository
Praat 음성 분석 데이터 관련 DB 작업을 처리하는 Repository
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.praat import PraatFeatures
from api.shared.repositories.base import BaseRepository


class PraatRepository(BaseRepository[PraatFeatures]):
    """Praat 음성 분석 Repository"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, PraatFeatures)
    
    async def create_and_flush(
        self,
        media_id: int,
        jitter_local: Optional[float] = None,
        shimmer_local: Optional[float] = None,
        hnr: Optional[float] = None,
        nhr: Optional[float] = None,
        f0: Optional[float] = None,
        max_f0: Optional[float] = None,
        min_f0: Optional[float] = None,
        cpp: Optional[float] = None,
        csid: Optional[float] = None,
        lh_ratio_mean_db: Optional[float] = None,
        lh_ratio_sd_db: Optional[float] = None,
        f1: Optional[float] = None,
        f2: Optional[float] = None,
        intensity_mean: Optional[float] = None
    ) -> PraatFeatures:
        """Praat 분석 결과 생성 (flush만 수행, commit은 호출자가 담당)"""
        praat_feature = PraatFeatures(
            media_id=media_id,
            jitter_local=jitter_local,
            shimmer_local=shimmer_local,
            hnr=hnr,
            nhr=nhr,
            f0=f0,
            max_f0=max_f0,
            min_f0=min_f0,
            cpp=cpp,
            csid=csid,
            lh_ratio_mean_db=lh_ratio_mean_db,
            lh_ratio_sd_db=lh_ratio_sd_db,
            f1=f1,
            f2=f2,
            intensity_mean=intensity_mean
            
        )
        
        self.db.add(praat_feature)
        await self.db.flush()  # commit 없이 flush만
        return praat_feature
    
    async def get_by_media_id(self, media_id: int) -> Optional[PraatFeatures]:
        """미디어 ID로 Praat 분석 결과 조회"""
        result = await self.db.execute(
            select(PraatFeatures).where(PraatFeatures.media_id == media_id)
        )
        return result.scalar_one_or_none()

