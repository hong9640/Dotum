/**
 * Praat 지표 타입 정의
 */
export type MaybeNum = number | null | undefined;

export type PraatValues = {
  // 켑스트럼/복합
  cpp?: MaybeNum; // dB, 정상 > 15
  csid?: MaybeNum; // 정상 < 3.0

  // 조화성/잡음·스펙트럼
  hnr?: MaybeNum; // dB, 정상 > 15
  nhr?: MaybeNum; // 정상 < 0.05
  lh_ratio_mean_db?: MaybeNum; // dB, 정상 -15 ~ -8
  lh_ratio_sd_db?: MaybeNum; // dB, 정상 < 3.0
  intensity?: MaybeNum; // dB, 정상 60~80

  // 퍼터베이션
  jitter_local?: MaybeNum; // %, 정상 < 0.02
  shimmer_local?: MaybeNum; // %, 정상 < 0.04

  // 기본 주파수
  f0?: MaybeNum; // Hz, 정상 150~250
  max_f0?: MaybeNum; // Hz, 정상 180~300
  min_f0?: MaybeNum; // Hz, 정상 120~200

  // 포먼트
  f1?: MaybeNum; // Hz, 정상 600~900
  f2?: MaybeNum; // Hz, 정상 1000~1500
};

export type PatientInfo = {
  analyzedAt?: string; // "2024년 1월 15일 14:30"
  word?: string; // 훈련 단어
};

