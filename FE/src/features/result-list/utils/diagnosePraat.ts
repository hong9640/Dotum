/**
 * Praat 지표를 기반으로 진단 문구를 생성하는 유틸리티
 */

interface PraatMetrics {
  jitter?: number | null;
  shimmer?: number | null;
}

/**
 * Praat 지표를 기반으로 진단 문구 생성
 * 
 * 기준:
 * - jitter > 0.012 and shimmer > 0.04: 이비인후과
 * - jitter > 0.012 or shimmer > 0.04 (둘 중 하나): 재활의학과
 * - else: 정상
 * 
 * @param metrics Praat 지표 (jitter, shimmer)
 * @returns 진단 문구
 */
export function diagnosePraat(metrics: PraatMetrics): string {
  const { jitter, shimmer } = metrics;
  
  // 값이 없으면 기본 메시지 반환
  if (jitter === null || jitter === undefined || shimmer === null || shimmer === undefined) {
    return '음성 분석 결과를 확인할 수 없습니다.';
  }
  
  const jitterThreshold = 0.012; // 1.2%
  const shimmerThreshold = 0.04; // 4%
  
  const jitterExceeded = jitter > jitterThreshold;
  const shimmerExceeded = shimmer > shimmerThreshold;
  
  // 둘 다 기준 초과: 이비인후과
  if (jitterExceeded && shimmerExceeded) {
    return '음성 분석 결과, 발성의 안정성과 소리 크기의 일관성에 문제가 감지되었습니다. 이비인후과 전문의 상담을 권장드립니다.';
  }
  
  // 둘 중 하나만 기준 초과: 재활의학과
  if (jitterExceeded || shimmerExceeded) {
    return '음성 분석 결과, 발성의 일부 지표에서 개선이 필요합니다. 재활의학과 전문의 상담을 권장드립니다.';
  }
  
  // 정상
  return '음성 분석 결과, 발성의 안정성과 소리 크기의 일관성이 정상 범위 내에 있습니다. 계속해서 꾸준히 연습하시면 더욱 좋아질 거예요.';
}

