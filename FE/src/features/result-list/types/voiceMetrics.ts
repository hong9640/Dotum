/**
 * 음성 분석 메트릭 타입 정의
 */

export interface VoiceMetrics {
  /** CPP (Cepstral Peak Prominence) */
  cpp: number | null;
  /** CSID (Cepstral/Spectral Index of Dysphonia) */
  csid: number | null;
  /** Jitter (지터) - 음성 떨림 */
  jitter: number | null;
  /** Shimmer (쉬머) - 음성 진폭 변동 */
  shimmer: number | null;
  /** NHR (Noise-to-Harmonics Ratio) */
  nhr: number | null;
  /** HNR (Harmonics-to-Noise Ratio) */
  hnr: number | null;
  /** 최대 F0 (기본 주파수) */
  maxF0: number | null;
  /** 최소 F0 (기본 주파수) */
  minF0: number | null;
  /** L/H Ratio Mean (dB) */
  lhRatioMeanDb: number | null;
  /** L/H Ratio SD (dB) */
  lhRatioSdDb: number | null;
}

/**
 * 빈 음성 메트릭 객체 생성
 */
export const createEmptyVoiceMetrics = (): VoiceMetrics => ({
  cpp: null,
  csid: null,
  jitter: null,
  shimmer: null,
  nhr: null,
  hnr: null,
  maxF0: null,
  minF0: null,
  lhRatioMeanDb: null,
  lhRatioSdDb: null,
});

/**
 * API 응답 데이터를 VoiceMetrics로 변환
 */
export const parseVoiceMetrics = (data: Record<string, unknown>): VoiceMetrics => ({
  cpp: (data.cpp as number) ?? null,
  csid: (data.csid as number) ?? null,
  jitter: (data.jitter_local as number) ?? (data.jitter as number) ?? null,
  shimmer: (data.shimmer_local as number) ?? (data.shimmer as number) ?? null,
  nhr: (data.nhr as number) ?? null,
  hnr: (data.hnr as number) ?? null,
  maxF0: (data.max_f0 as number) ?? null,
  minF0: (data.min_f0 as number) ?? null,
  lhRatioMeanDb: (data.lh_ratio_mean_db as number) ?? null,
  lhRatioSdDb: (data.lh_ratio_sd_db as number) ?? null,
});

