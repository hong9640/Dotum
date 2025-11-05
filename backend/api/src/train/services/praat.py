import io
import json
import asyncio
import pathlib
import numpy as np
import parselmouth
import soundfile as sf
from parselmouth.praat import call
from scipy.signal import get_window
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Optional
from api.src.train.models.praat import PraatFeatures
from api.src.train.models.media import MediaFile, MediaType
from api.src.train.repositories.training_items import TrainingItemRepository
from api.src.train.services.media import MediaService
from api.src.user.user_model import User
from ..repositories.training_items import TrainingItemRepository
from ..repositories.training_sessions import TrainingSessionRepository

# ============================
# 1. 파라미터 정의
# ============================
PITCH_FLOOR = 75
PITCH_CEIL = 600
LH_SPLIT_HZ = 4000.0
CPPS_FS_TARGET = 16000
CPPS_FRAME_LEN = 0.01
CPPS_HOP_LEN = 0.005
CPPS_EPS = 1e-12
LH_FRAME_LEN = 0.05
LH_HOP_LEN = 0.025
INTENSITY_MIN_DB = 100
INTENSITY_TIME_STEP = 0.025
PITCH_TIME_STEP = 0.0

PITCH_CEILING = 500.0
JITTER_SHIMMER_COMMON_ARGS = (0, 0, 0.0001, 0.02, 1.3)
SHIMMER_EXTRA_ARGS = (1.6,)
# ============================
# 2. 도우미 함수
# ============================
def _extract_mono(snd: parselmouth.Sound) -> parselmouth.Sound:
    """사운드 객체에서 단일 채널을 추출합니다."""
    if snd.n_channels == 2:
        return call(snd, "Extract one channel...", 1)
    return snd

def compute_cpp_numpy(snd: parselmouth.Sound, fmin: float = 60.0, fmax: float = 330.0) -> float:
    """CPPS (Cepstral Peak Prominence Smoothed) 값을 계산합니다."""
    snd = _extract_mono(snd)
    if snd.sampling_frequency != CPPS_FS_TARGET:
        snd = parselmouth.praat.call(snd, "Resample...", CPPS_FS_TARGET, 50)
    sr = int(snd.sampling_frequency)
    x = snd.values[0].astype(np.float64)
    n_frame = int(round(CPPS_FRAME_LEN * sr))
    n_hop = int(round(CPPS_HOP_LEN * sr))
    win = get_window("hamming", n_frame, fftbins=True)
    qmin = 1.0 / fmax
    qmax = 1.0 / fmin
    cpp_list = []
    i = 0
    while i + n_frame <= len(x):
        seg = x[i:i + n_frame] * win
        i += n_hop
        spec = np.fft.rfft(seg)
        mag = np.abs(spec) + CPPS_EPS
        log_mag = np.log(mag)
        cep = np.fft.irfft(log_mag)
        q = np.arange(len(cep)) / sr
        mask = (q >= qmin) & (q <= qmax)
        if not np.any(mask):
            continue
        y = cep[mask]
        xq = q[mask]
        coef = np.polyfit(xq, y, 1)
        trend = np.polyval(coef, xq)
        peak_val = np.max(y)
        peak_idx = np.argmax(y)
        trend_at_peak = trend[peak_idx]
        cpp = (peak_val - trend_at_peak) * 20 / np.log(10)
        cpp_list.append(cpp)
    return float(np.mean(cpp_list)) if cpp_list else float("nan")

def compute_lh_ratio_series(snd: parselmouth.Sound) -> np.ndarray:
    """L/H Ratio (Low-to-High frequency energy ratio) 시계열 데이터를 계산합니다."""
    snd = _extract_mono(snd)
    sr = snd.sampling_frequency
    signal = snd.values[0]
    lh_db_list = []
    frame_n = int(round(LH_FRAME_LEN * sr))
    hop_n = int(round(LH_HOP_LEN * sr))
    if frame_n <= 0 or hop_n <= 0:
        return np.array([])
    for start in range(0, len(signal) - frame_n + 1, hop_n):
        frame = signal[start:start + frame_n]
        win = get_window("hamming", len(frame))
        x = frame * win
        spec = np.fft.rfft(x)
        mag2 = np.abs(spec) ** 2
        freqs = np.fft.rfftfreq(len(x), d=1.0 / sr)
        low_mask = freqs <= LH_SPLIT_HZ
        high_mask = freqs > LH_SPLIT_HZ
        low_e = float(np.sum(mag2[low_mask])) + CPPS_EPS
        high_e = float(np.sum(mag2[high_mask])) + CPPS_EPS
        lh_db = 10.0 * np.log10(low_e / high_e)
        lh_db_list.append(lh_db)
    return np.array(lh_db_list, dtype=float)

def estimate_csid_awan2016(cpp: float, lh_series_db: np.ndarray) -> float:
    """CSID (Cepstral/Spectral Index of Dysphonia) 값을 추정합니다."""
    if lh_series_db.size == 0 or not np.isfinite(cpp):
        return float("nan")
    lh_mean = float(np.mean(lh_series_db))
    lh_sd = float(np.std(lh_series_db, ddof=1)) if lh_series_db.size > 1 else 0.0
    csid = 154.59 - (10.39 * cpp) - (1.08 * lh_mean) - (3.71 * lh_sd)
    return float(csid)


# ============================
# 3. 메인 추출 함수
# ============================
async def extract_all_features(voice_data: bytes) -> dict:
    """
    음성 데이터에서 CPPS, CSID 및 시계열 데이터를 추출하여 딕셔너리로 반환합니다.
    """
    try:
        samples, sampling_frequency = sf.read(io.BytesIO(voice_data))
        
        # 스테레오(2D 배열)인 경우, 채널을 평균내어 모노(1D 배열)로 변환
        if samples.ndim == 2:
            samples = samples.mean(axis=1)

        snd = parselmouth.Sound(samples, sampling_frequency=sampling_frequency)

        # 음높이(Pitch)와 관련 객체 생성
        point_process = parselmouth.praat.call(snd, "To PointProcess (periodic, cc)", PITCH_FLOOR, PITCH_CEILING)
        pitch = snd.to_pitch(pitch_floor=PITCH_FLOOR, pitch_ceiling=PITCH_CEILING)
        harmonicity = snd.to_harmonicity(minimum_pitch=PITCH_FLOOR)

        # CPPS, L/H ratio, CSID 계산
        cpp = compute_cpp_numpy(snd)
        lh_series = compute_lh_ratio_series(snd)
        csid = estimate_csid_awan2016(cpp, lh_series)

        cpp_csid_features = {
            "cpp": cpp,
            "csid": csid
        }

        jitter_types = ["local"]
        jitter_features = {
            f"jitter_{j_type}": parselmouth.praat.call(point_process, f"Get jitter ({j_type})", *JITTER_SHIMMER_COMMON_ARGS)
            for j_type in jitter_types
        }

        shimmer_types = ["local"]
        shimmer_features = {
            f"shimmer_{s_type}": parselmouth.praat.call(
                (snd, point_process), f"Get shimmer ({s_type})", *JITTER_SHIMMER_COMMON_ARGS, *SHIMMER_EXTRA_ARGS
            )
            for s_type in shimmer_types
        }

        hnr = parselmouth.praat.call(harmonicity, "Get mean", 0, 0)
        nhr = 10 ** (-hnr / 10) if hnr > 0 else 0.0

        f0 = parselmouth.praat.call(pitch, "Get mean", 0, 0, "Hertz")
        max_f0 = parselmouth.praat.call(pitch, "Get maximum", 0, 0, "Hertz", "Parabolic")
        min_f0 = parselmouth.praat.call(pitch, "Get minimum", 0, 0, "Hertz", "Parabolic")

        other_features = {
            "hnr": hnr,
            "nhr": nhr,
            "f0": f0,
            "max_f0": max_f0,
            "min_f0": min_f0,
        }

        final_features = {
            **cpp_csid_features,  # cpp, csid
            **jitter_features,    # jitter_local
            **shimmer_features,   # shimmer_local
            **other_features      # hnr, nhr, f0, max_f0, min_f0
        }
        
        return final_features

    except Exception as e:
        # 포괄적인 예외 처리
        raise ValueError(f"전체 특징 추출 중 오디오 데이터 처리 오류: {e}")

async def get_praat_analysis_from_db(
    db: AsyncSession,
    session_id: int,
    item_id: int,
    user_id: int,
) -> Optional[PraatFeatures]:
    """
    특정 훈련 아이템(item_id)의 Praat 분석 결과를 조회합니다.
    소유권을 먼저 확인하고, 연결된 오디오 파일의 분석 결과를 찾습니다.
    """
    item_repo = TrainingItemRepository(db)
    media_service = MediaService(db)

    # 1. 훈련 아이템 조회 및 소유권 확인 (media_file도 함께 로드)
    item = await item_repo.get_item(session_id, item_id, include_relations=True)
    if not item:
        raise LookupError("훈련 아이템을 찾을 수 없습니다.")

    # 2. 비디오 미디어 파일 조회
    if not item.media_file_id:
        # 비디오가 아직 업로드되지 않았으므로 분석 결과도 없음
        return None

    # Eager loading으로 이미 로드된 media_file 사용 (DB 조회 방지)
    video_media = item.media_file
    if not video_media:
        raise LookupError("연결된 비디오 미디어 파일을 찾을 수 없습니다.")

    # 3. 소유권 확인
    if video_media.user_id != user_id:
        raise PermissionError("접근 권한이 없습니다.")

    # 4. 비디오 object_key를 기반으로 오디오 object_key 추론
    audio_object_key = video_media.object_key.replace('.mp4', '.wav')
    audio_media = await media_service.get_media_file_by_object_key(audio_object_key)
    if not audio_media:
        return None

    # 5. Praat 분석 결과 조회
    statement_praat = select(PraatFeatures).where(PraatFeatures.media_id == audio_media.id)
    result_praat = await db.execute(statement_praat)
    analysis = result_praat.scalars().first()

    return analysis