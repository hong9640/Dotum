from datetime import datetime
from typing import Optional, List
from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from api.src.train.models.training_session import TrainingSession, TrainingType
from api.src.train.models.training_item import TrainingItem
from api.src.train.models.media import MediaFile
from api.src.train.models.praat import PraatFeatures
from api.src.train.models.session_praat_result import SessionPraatResult
from api.src.train.repositories.training_items import TrainingItemRepository
from api.src.train.services.media import MediaService


async def save_session_praat_result(
    db: AsyncSession, 
    session_id: int, 
    session: Optional[TrainingSession] = None
) -> Optional[SessionPraatResult]:
    """
    - vocal 타입 세션의 PraatFeatures를 범위별로 평균내어 SessionPraatResult 테이블에 저장합니다.
    
    범위 계산:
    - n = total_items / 5 (프론트에서 받은 반복 횟수)
    - 첫 번째 그룹 (0 ~ (1 * n) - 1): jitter_local, shimmer_local, nhr, hnr, lh_ratio_mean_db, lh_ratio_sd_db
      (0번째 아이템의 시도 1, 2, ... n)
    - 두 번째 그룹 ((1 * n) ~ (5 * n) - 1): max_f0, min_f0, intensity_mean
      (1번째 아이템 ~ 4번째 아이템)
    - 전체 (0 ~ (5 * n) - 1): f0, f1, f2
      (0번째 아이템 ~ 4번째 아이템)
    
    - Praat 데이터가 일부만 있거나 전혀 없어도 안전하게 처리합니다.
    - 이미 존재하면 UPDATE, 없으면 INSERT 합니다.
    
    Args:
        db: 데이터베이스 세션
        session_id: 훈련 세션 ID
        session: 훈련 세션 객체 (전달되면 재조회 생략하여 성능 최적화)
    """
    # 1. 세션 조회 및 vocal 타입 확인 (이미 조회된 세션이 있으면 재조회 생략)
    if session is None:
        session_stmt = select(TrainingSession).where(TrainingSession.id == session_id)
        session_result = await db.execute(session_stmt)
        session = session_result.scalar_one_or_none()
    
    if not session:
        print(f"⚠️ Session {session_id}: 세션을 찾을 수 없습니다.")
        return None
    
    if session.type != TrainingType.VOCAL:
        print(f"⚠️ Session {session_id}: vocal 타입이 아니어서 평균 계산을 건너뜁니다. (타입: {session.type})")
        return None
    
    # 2. n 값 계산
    if session.total_items == 0:
        print(f"⚠️ Session {session_id}: 아이템이 없어 평균 계산을 건너뜁니다.")
        return None
    
    n = session.total_items / 5
    if n < 1:
        print(f"⚠️ Session {session_id}: n 값이 1보다 작아 평균 계산을 건너뜁니다. (n={n})")
        return None
    
    # 3. 세션의 모든 아이템을 item_index 순서로 가져오기
    item_repo = TrainingItemRepository(db)
    items = await item_repo.get_session_items(session_id, include_relations=True)
    
    if not items:
        print(f"⚠️ Session {session_id}: 훈련 아이템을 찾을 수 없습니다.")
        return None
    
    # item_index 순서로 정렬 (이미 정렬되어 있을 수 있지만 확실히)
    items = sorted(items, key=lambda x: x.item_index)
    
    # 4. 각 아이템의 PraatFeatures 조회
    media_service = MediaService(db)
    praat_features_list: List[tuple[int, PraatFeatures]] = []  # (item_index, PraatFeatures)
    
    for item in items:
        if not item.media_file_id:
            continue
        
        # VOCAL 타입: media_file_id를 직접 사용 (오디오 파일이 직접 저장됨)
        # WORD/SENTENCE 타입: video media에서 audio media를 찾아서 사용
        audio_media_id = None
        
        if session.type == TrainingType.VOCAL:
            # VOCAL 타입은 media_file_id에 오디오 파일이 직접 저장되어 있음
            audio_media_id = item.media_file_id
        else:
            # WORD/SENTENCE 타입: video media에서 audio media 찾기
            # Eager loading으로 이미 로드된 media_file 사용
            video_media = item.media_file
            if not video_media or not video_media.object_key:
                continue
            
            # 비디오 object_key를 오디오 object_key로 변환
            if not video_media.object_key.endswith('.mp4'):
                continue
            
            audio_object_key = video_media.object_key.replace('.mp4', '.wav')
            audio_media = await media_service.get_media_file_by_object_key(audio_object_key)
            
            if not audio_media:
                continue
            
            audio_media_id = audio_media.id
        
        # PraatFeatures 조회
        if audio_media_id:
            praat_stmt = select(PraatFeatures).where(PraatFeatures.media_id == audio_media_id)
            praat_result = await db.execute(praat_stmt)
            praat_feature = praat_result.scalar_one_or_none()
            
            if praat_feature:
                praat_features_list.append((item.item_index, praat_feature))
    
    if not praat_features_list:
        print(f"⚠️ Session {session_id}: Praat 데이터가 없어 평균 계산을 건너뜁니다.")
        return None
    
    # 5. 범위별 평균 계산
    n_int = int(n)
    
    # 첫 번째 그룹: 0 ~ n-1
    first_group = [
        pf for idx, pf in praat_features_list
        if 0 <= idx < n_int
    ]
    
    # 두 번째 그룹: n ~ 5n-1
    second_group = [
        pf for idx, pf in praat_features_list
        if n_int <= idx < (5 * n_int)
    ]
    
    # 전체 그룹: 0 ~ 5n-1
    all_group = [
        pf for idx, pf in praat_features_list
        if 0 <= idx < (5 * n_int)
    ]
    
    # 평균 계산 헬퍼 함수
    def calc_avg(values: List[Optional[float]]) -> Optional[float]:
        """None이 아닌 값들의 평균 계산"""
        valid_values = [v for v in values if v is not None]
        if not valid_values:
            return None
        return sum(valid_values) / len(valid_values)
    
    # 첫 번째 그룹 평균 (0 ~ (1 * n) - 1)
    avg_jitter_local = calc_avg([pf.jitter_local for pf in first_group])
    avg_shimmer_local = calc_avg([pf.shimmer_local for pf in first_group])
    avg_nhr = calc_avg([pf.nhr for pf in first_group])
    avg_hnr = calc_avg([pf.hnr for pf in first_group])
    avg_lh_ratio_mean_db = calc_avg([pf.lh_ratio_mean_db for pf in first_group])
    avg_lh_ratio_sd_db = calc_avg([pf.lh_ratio_sd_db for pf in first_group])
    
    # 두 번째 그룹 평균 ((1 * n) ~ (5 * n) - 1)
    avg_max_f0 = calc_avg([pf.max_f0 for pf in second_group])
    avg_min_f0 = calc_avg([pf.min_f0 for pf in second_group])
    avg_intensity_mean = calc_avg([pf.intensity_mean for pf in second_group])
    
    # 전체 그룹 평균 (0 ~ (5 * n) - 1)
    avg_f0 = calc_avg([pf.f0 for pf in all_group])
    avg_f1 = calc_avg([pf.f1 for pf in all_group])
    avg_f2 = calc_avg([pf.f2 for pf in all_group])
    
    # 6. 기존 세션 평균 기록이 있는지 확인
    existing_stmt = select(SessionPraatResult).where(
        SessionPraatResult.training_session_id == session_id
    )
    existing_result = await db.execute(existing_stmt)
    existing_record = existing_result.scalars().first()
    
    # 7. 업데이트 또는 새로 생성
    if existing_record:
        existing_record.avg_jitter_local = avg_jitter_local
        existing_record.avg_shimmer_local = avg_shimmer_local
        existing_record.avg_nhr = avg_nhr
        existing_record.avg_hnr = avg_hnr
        existing_record.avg_lh_ratio_mean_db = avg_lh_ratio_mean_db
        existing_record.avg_lh_ratio_sd_db = avg_lh_ratio_sd_db
        existing_record.avg_max_f0 = avg_max_f0
        existing_record.avg_min_f0 = avg_min_f0
        existing_record.avg_intensity_mean = avg_intensity_mean
        existing_record.avg_f0 = avg_f0
        existing_record.avg_f1 = avg_f1
        existing_record.avg_f2 = avg_f2
        existing_record.updated_at = datetime.utcnow()
        
        print(f"🌀 Session {session_id}: 기존 평균 Praat 결과 갱신 완료 (n={n}, 첫 그룹={len(first_group)}, 두 번째 그룹={len(second_group)}, 전체={len(all_group)})")
    else:
        new_record = SessionPraatResult(
            training_session_id=session_id,
            avg_jitter_local=avg_jitter_local,
            avg_shimmer_local=avg_shimmer_local,
            avg_nhr=avg_nhr,
            avg_hnr=avg_hnr,
            avg_lh_ratio_mean_db=avg_lh_ratio_mean_db,
            avg_lh_ratio_sd_db=avg_lh_ratio_sd_db,
            avg_max_f0=avg_max_f0,
            avg_min_f0=avg_min_f0,
            avg_intensity_mean=avg_intensity_mean,
            avg_f0=avg_f0,
            avg_f1=avg_f1,
            avg_f2=avg_f2,
        )
        db.add(new_record)
        existing_record = new_record
        print(f"✅ Session {session_id}: 평균 Praat 결과 새로 저장 (n={n}, 첫 그룹={len(first_group)}, 두 번째 그룹={len(second_group)}, 전체={len(all_group)})")
    
    await db.commit()
    await db.refresh(existing_record)
    
    return existing_record

