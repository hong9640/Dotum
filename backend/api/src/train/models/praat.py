from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from api.src.train.models.media import MediaFile


class PraatFeatures(SQLModel, table=True):
    """Praat 지표 저장 테이블"""
    __tablename__ = "praat_features"
    id: int = Field(default=None, primary_key=True)
    media_id: int = Field(index=True, description="미디어 id(논리 fk)")
    jitter_local: Optional[float] = None
    shimmer_local: Optional[float] = None
    hnr: Optional[float] = None
    nhr: Optional[float] = None
    f0: Optional[float] = None
    max_f0: Optional[float] = None
    min_f0: Optional[float] = None
    cpp: Optional[float] = None
    csid: Optional[float] = None

    # 관계 (논리 FK)
    user: Optional["MediaFile"] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "PraatFeatures.media_id==foreign(MediaFile.id)",
            "foreign_keys": "[PraatFeatures.media_id]",
        }
    )


