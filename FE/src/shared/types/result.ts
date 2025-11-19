import type React from 'react';

/**
 * 결과 평가 및 피드백 관련 공통 타입 정의
 */

/**
 * 평가 상태 타입
 */
export type EvaluationStatus = "좋음" | "주의" | "개선 필요";

/**
 * 상세 평가 항목 타입
 */
export interface DetailedEvaluationItem {
  id: string;
  title: string;
  status: EvaluationStatus;
  icon: React.ElementType;
  content?: string; // 피드백 내용
}

/**
 * 아이템 피드백 타입 (GPT 피드백 구조)
 */
export interface ItemFeedback {
  item?: string; // 한 줄 요약
  vowel_distortion?: string; // 모음 왜곡도
  sound_stability?: string; // 소리의 안정도
  voice_clarity?: string; // 음성 일탈도
  voice_health?: string; // 음성 건강지수
}

/**
 * FeedbackCard Props 타입
 */
export interface FeedbackCardProps {
  hideSections?: boolean; // 일부 섹션 숨김 여부
  praatData?: unknown; // PraatMetrics 타입은 feature에서 정의되므로 unknown으로 처리
  praatLoading?: boolean;
  feedback?: ItemFeedback | null;
}

/**
 * DetailedEvaluationItems Props 타입
 */
export interface DetailedEvaluationItemsProps {
  praatData?: unknown; // PraatMetrics 타입은 feature에서 정의되므로 unknown으로 처리
  feedback?: ItemFeedback | null;
}

/**
 * FeedbackSummary Props 타입
 */
export interface FeedbackSummaryProps {
  feedback?: string;
}

