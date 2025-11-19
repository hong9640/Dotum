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
from api.modules.training.models.praat import PraatFeatures
from api.modules.training.models.media import MediaFile, MediaType
from api.modules.training.repositories.training_items import TrainingItemRepository
from api.modules.training.repositories.training_sessions import TrainingSessionRepository
from api.modules.training.services.media import MediaService
from api.modules.user.models.model import User

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
def _safe_float(v) -> Optional[float]:
    """
    NaN, Infinity, -Infinity 값을 None으로 변환하는 안전한 float 변환 함수.
    넘파이 스칼라도 처리합니다.
    """
    if v is None:
        return None
    
    # 넘파이 스칼라 처리
    try:
        if isinstance(v, (np.floating, np.integer)):
            v = float(v)
    except Exception:
        pass
    
    # float 타입 확인 및 유한성 검사
    if isinstance(v, float):
        if not np.isfinite(v):
            return None
        return v
    
    # 다른 타입은 그대로 반환 (int 등)
    try:
        v_float = float(v)
        if not np.isfinite(v_float):
            return None
        return v_float
    except (ValueError, TypeError):
        return None

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
    result = float(np.mean(cpp_list)) if cpp_list else None
    return _safe_float(result)

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

def estimate_csid_awan2016(cpp: float, lh_series_db: np.ndarray) -> Optional[float]:
    """CSID (Cepstral/Spectral Index of Dysphonia) 값을 추정합니다."""
    if lh_series_db.size == 0 or cpp is None or not np.isfinite(cpp):
        return None
    lh_mean = float(np.mean(lh_series_db))
    lh_sd = float(np.std(lh_series_db, ddof=1)) if lh_series_db.size > 1 else 0.0
    csid = 154.59 - (10.39 * cpp) - (1.08 * lh_mean) - (3.71 * lh_sd)
    return _safe_float(float(csid))


# ============================
# 3. 메인 추출 함수
# ============================
async def extract_all_features(voice_data: bytes) -> dict:
    """
    음성 데이터에서 CPPS, CSID 및 시계열 데이터를 추출하여 딕셔너리로 반환합니다.
    
    지원 형식: WAV, FLAC, OGG (soundfile이 직접 지원)
    MP3 등 다른 형식은 자동으로 WAV로 변환 시도합니다.
    """
    # 먼저 soundfile로 직접 읽기 시도
    try:
        samples, sampling_frequency = sf.read(io.BytesIO(voice_data))
    except (sf.LibsndfileError, Exception) as e:
        # soundfile이 인식하지 못하는 형식인 경우 (예: MP3)
        # FFmpeg를 사용하여 WAV로 변환 시도
        try:
            from ..services.video import VideoProcessor
            video_processor = VideoProcessor()
            
            # MP3 등 다른 형식을 WAV로 변환
            wav_data = await video_processor.convert_mp3_to_wav(voice_data)
            
            # 변환된 WAV 파일로 다시 읽기
            samples, sampling_frequency = sf.read(io.BytesIO(wav_data))
        except Exception as convert_error:
            # 변환도 실패한 경우
            raise ValueError(
                f"오디오 파일 형식을 인식할 수 없습니다. "
                f"WAV, FLAC, OGG 형식의 파일을 업로드해주세요. "
                f"(원본 에러: {type(e).__name__}: {e}, 변환 시도 에러: {type(convert_error).__name__}: {convert_error})"
            )
    
    try:
        
        # 스테레오(2D 배열)인 경우, 채널을 평균내어 모노(1D 배열)로 변환
        if samples.ndim == 2:
            samples = samples.mean(axis=1)

        snd = parselmouth.Sound(samples, sampling_frequency=sampling_frequency)

        # 음높이(Pitch)와 관련 객체 생성
        point_process = parselmouth.praat.call(snd, "To PointProcess (periodic, cc)", PITCH_FLOOR, PITCH_CEILING)
        pitch = snd.to_pitch(pitch_floor=PITCH_FLOOR, pitch_ceiling=PITCH_CEILING)
        harmonicity = snd.to_harmonicity(minimum_pitch=PITCH_FLOOR)
        
        # Intensity 객체 생성
        intensity = snd.to_intensity(minimum_pitch=PITCH_FLOOR, time_step=INTENSITY_TIME_STEP)

        # CPPS, L/H ratio, CSID 계산
        cpp = compute_cpp_numpy(snd)
        lh_series = compute_lh_ratio_series(snd)
        csid = estimate_csid_awan2016(cpp, lh_series)
        
        # L/H ratio 평균 및 표준편차 계산
        lh_ratio_mean_db = _safe_float(float(np.mean(lh_series))) if lh_series.size > 0 else None
        lh_ratio_sd_db = _safe_float(float(np.std(lh_series, ddof=1))) if lh_series.size > 1 else None

        # 포먼트(Formant) 추출
        formant = snd.to_formant_burg(time_step=0.01, max_number_of_formants=5, 
                                       maximum_formant=5500, window_length=0.025, 
                                       pre_emphasis_from=50)

        cpp_csid_features = {
            "cpp": cpp,
            "csid": csid,
            "lh_ratio_mean_db": lh_ratio_mean_db,
            "lh_ratio_sd_db": lh_ratio_sd_db
        }

        jitter_types = ["local"]
        jitter_features = {
            f"jitter_{j_type}": _safe_float(parselmouth.praat.call(point_process, f"Get jitter ({j_type})", *JITTER_SHIMMER_COMMON_ARGS))
            for j_type in jitter_types
        }

        shimmer_types = ["local"]
        shimmer_features = {
            f"shimmer_{s_type}": _safe_float(parselmouth.praat.call(
                (snd, point_process), f"Get shimmer ({s_type})", *JITTER_SHIMMER_COMMON_ARGS, *SHIMMER_EXTRA_ARGS
            ))
            for s_type in shimmer_types
        }

        hnr_raw = parselmouth.praat.call(harmonicity, "Get mean", 0, 0)
        hnr = _safe_float(hnr_raw)
        nhr = _safe_float(10 ** (-hnr_raw / 10)) if hnr_raw > 0 else 0.0

        f0_raw = parselmouth.praat.call(pitch, "Get mean", 0, 0, "Hertz")
        f0 = _safe_float(f0_raw)
        max_f0_raw = parselmouth.praat.call(pitch, "Get maximum", 0, 0, "Hertz", "Parabolic")
        max_f0 = _safe_float(max_f0_raw)
        min_f0_raw = parselmouth.praat.call(pitch, "Get minimum", 0, 0, "Hertz", "Parabolic")
        min_f0 = _safe_float(min_f0_raw)

        # 포먼트(Formant) 추출
        f1_raw = parselmouth.praat.call(formant, "Get mean", 1, 0, 0, "Hertz")
        f1 = _safe_float(f1_raw)
        f2_raw = parselmouth.praat.call(formant, "Get mean", 2, 0, 0, "Hertz")
        f2 = _safe_float(f2_raw)

        # Intensity 값 추출
        intensity_mean_raw = parselmouth.praat.call(intensity, "Get mean", 0, 0, "dB")
        intensity_mean = _safe_float(intensity_mean_raw)

        other_features = {
            "hnr": hnr,
            "nhr": nhr,
            "f0": f0,
            "max_f0": max_f0,
            "min_f0": min_f0,
            "f1": f1,
            "f2": f2,
            "intensity_mean": intensity_mean,
        }

        final_features = {
            **cpp_csid_features,  # cpp, csid, lh_ratio_mean_db, lh_ratio_sd_db
            **jitter_features,    # jitter_local
            **shimmer_features,   # shimmer_local
            **other_features      # hnr, nhr, f0, max_f0, min_f0, f1, f2
        }
        
        return final_features

    except ValueError:
        # 이미 변환된 에러는 그대로 재발생
        raise
    except Exception as e:
        # 포괄적인 예외 처리
        raise ValueError(f"전체 특징 추출 중 오디오 데이터 처리 오류: {type(e).__name__}: {e}")

async def get_praat_analysis_from_db(
    db: AsyncSession,
    session_id: int,
    item_id: int,
    user_id: int,
):
    """
    특정 훈련 아이템(item_id)의 Praat 분석 결과를 조회합니다.
    소유권을 먼저 확인하고, 연결된 오디오 파일의 분석 결과를 찾습니다.
    
    VOCAL 타입: item.media_file_id는 이미지 파일이므로, 오디오 파일을 별도로 찾습니다.
    WORD/SENTENCE 타입: item.media_file_id는 비디오 파일이므로, .mp4 -> .wav 치환 로직을 사용합니다.
    
    VOCAL 세션일 경우 image_url도 함께 반환합니다.
    """
    from ..models.training_session import TrainingSession, TrainingType
    from ..models.media import MediaFile, MediaType
    from ..schemas.praat import PraatFeaturesResponse
    
    item_repo = TrainingItemRepository(db)
    media_service = MediaService(db)

    # 1. 훈련 아이템 조회 및 소유권 확인 (media_file도 함께 로드)
    item = await item_repo.get_item(session_id, item_id, include_relations=True)
    if not item:
        raise LookupError("훈련 아이템을 찾을 수 없습니다.")

    # 2. 세션 타입 확인
    session_stmt = select(TrainingSession).where(TrainingSession.id == session_id)
    session_result = await db.execute(session_stmt)
    session = session_result.scalar_one_or_none()
    if not session:
        raise LookupError("훈련 세션을 찾을 수 없습니다.")
    
    # 세션 소유권 확인
    if session.user_id != user_id:
        raise PermissionError("접근 권한이 없습니다.")

    # 3. VOCAL 타입과 WORD/SENTENCE 타입 분기 처리
    audio_media_id = None
    
    if session.type == TrainingType.VOCAL:
        # VOCAL 타입: item.media_file_id가 이미 오디오 MediaFile ID를 가리킴
        # (submit_vocal_item에서 audio_media_file.id로 저장됨)
        if not item.media_file_id:
            # 오디오가 아직 업로드되지 않았으므로 분석 결과도 없음
            return None
        
        # Eager loading으로 이미 로드된 media_file 사용
        audio_media = item.media_file
        if not audio_media:
            raise LookupError("연결된 오디오 미디어 파일을 찾을 수 없습니다.")
        
        # 소유권 확인
        if audio_media.user_id != user_id:
            raise PermissionError("접근 권한이 없습니다.")
        
        audio_media_id = audio_media.id
    else:
        # WORD/SENTENCE 타입: video media에서 audio media 찾기
        if not item.media_file_id:
            # 비디오가 아직 업로드되지 않았으므로 분석 결과도 없음
            return None

        # Eager loading으로 이미 로드된 media_file 사용 (DB 조회 방지)
        video_media = item.media_file
        if not video_media:
            raise LookupError("연결된 비디오 미디어 파일을 찾을 수 없습니다.")

        # 소유권 확인
        if video_media.user_id != user_id:
            raise PermissionError("접근 권한이 없습니다.")

        # 비디오 object_key를 기반으로 오디오 object_key 추론
        if not video_media.object_key or not video_media.object_key.endswith('.mp4'):
            return None
        
        audio_object_key = video_media.object_key.replace('.mp4', '.wav')
        audio_media = await media_service.get_media_file_by_object_key(audio_object_key)
        if not audio_media:
            return None
        
        audio_media_id = audio_media.id

    # 4. Praat 분석 결과 조회
    if not audio_media_id:
        return None
    
    statement_praat = select(PraatFeatures).where(PraatFeatures.media_id == audio_media_id)
    result_praat = await db.execute(statement_praat)
    analysis = result_praat.scalars().first()

    if not analysis:
        return None

    # PraatFeatures 모델을 딕셔너리로 변환 (model_dump 사용)
    analysis_dict = analysis.model_dump()
    if session.type == TrainingType.VOCAL:
        analysis_dict["image_url"] = item.image_url

    return PraatFeaturesResponse(**analysis_dict)