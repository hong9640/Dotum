/**
 * 세션 상세 데이터 변환 유틸리티
 */
import type { WordResult } from "../types";
import type { SessionDetailResponse } from "../api/session-detail-search";
import type { VoiceMetrics } from "../types";
import { createEmptyVoiceMetrics } from "../types";
import { diagnosePraat } from "./diagnosePraat";

/**
 * 발성 연습 이름 목록
 */
const VOCAL_TRAINING_NAMES = [
  '최대 발성 지속 시간 연습 (MPT)',
  '크레셴도 연습 (점강)',
  '데크레셴도 연습 (점약)',
  '순간 강약 전환 연습',
  '연속 강약 조절 연습'
] as const;

/**
 * 세션 타입이 발성 연습인지 확인
 */
export const isVoiceTraining = (sessionType: string, typeParam?: string | null): boolean => {
  const sessionTypeLower = sessionType.toLowerCase();
  return sessionTypeLower === 'vocal' || (typeParam?.toLowerCase() === 'vocal');
};

/**
 * 세션 상세 데이터를 WordResult 배열로 변환
 */
export const transformToWordResults = (
  sessionDetail: SessionDetailResponse,
  isVoice: boolean
): WordResult[] => {
  if (isVoice) {
    // 발성 연습: 고정된 5개 연습명 반환
    return VOCAL_TRAINING_NAMES.map((trainingName, index) => ({
      id: index + 1,
      word: trainingName,
      feedback: null,
      score: 0,
    }));
  }

  // 일반 연습: 완료된 아이템만 필터링하여 변환
  const completedItems = sessionDetail.training_items?.filter(
    (item) => item.is_completed
  ) ?? [];

  // item_index 기준으로 오름차순 정렬
  const sortedCompletedItems = [...completedItems].sort(
    (a, b) => (a.item_index || 0) - (b.item_index || 0)
  );

  return sortedCompletedItems.map((item) => {
    const text = item.word || item.sentence || '';
    return {
      id: item.item_index + 1,
      word: text,
      feedback: item.feedback || null,
      score: item.score ?? 0,
    };
  });
};

/**
 * 세션 상세 데이터에서 VoiceMetrics 추출
 */
export const extractVoiceMetrics = (
  sessionDetail: SessionDetailResponse,
  isVoice: boolean
): VoiceMetrics => {
  const praatResult = sessionDetail.session_praat_result;

  if (!praatResult) {
    return createEmptyVoiceMetrics();
  }

  if (isVoice) {
    // 발성 연습: 8개 메트릭
    return {
      cpp: null,
      csid: null,
      jitter: praatResult.avg_jitter_local ?? null,
      shimmer: praatResult.avg_shimmer_local ?? null,
      nhr: praatResult.avg_nhr ?? null,
      hnr: praatResult.avg_hnr ?? null,
      maxF0: praatResult.avg_max_f0 ?? null,
      minF0: praatResult.avg_min_f0 ?? null,
      lhRatioMeanDb: praatResult.avg_lh_ratio_mean_db ?? null,
      lhRatioSdDb: praatResult.avg_lh_ratio_sd_db ?? null,
    };
  }

  // 일반 연습: CPP/CSID만
  return {
    ...createEmptyVoiceMetrics(),
    cpp: praatResult.avg_cpp ?? null,
    csid: praatResult.avg_csid ?? null,
  };
};

/**
 * 세션 상세 데이터에서 전체 피드백 추출
 */
export const extractOverallFeedback = (
  sessionDetail: SessionDetailResponse,
  isVoice: boolean
): string | null => {
  if (isVoice) {
    // 발성 연습: Praat 지표 기반 진단
    const praatResult = sessionDetail.session_praat_result;
    if (!praatResult) {
      return null;
    }
    return diagnosePraat({
      jitter: praatResult.avg_jitter_local ?? null,
      shimmer: praatResult.avg_shimmer_local ?? null,
    });
  }

  // 일반 연습: 백엔드에서 제공하는 overall_feedback 사용
  return sessionDetail.overall_feedback || null;
};

