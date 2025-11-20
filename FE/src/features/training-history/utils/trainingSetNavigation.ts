/**
 * TrainingSet 네비게이션 관련 유틸리티
 */
import type { TrainingSet } from "../types";
import { formatDateForUrl } from "./calendar";

/**
 * TrainingSet 클릭 시 이동할 경로 계산
 */
export const calculateTrainingSetPath = (
  trainingSet: TrainingSet,
  date: string
): string | null => {
  // 완료된 세션은 result-list 페이지로 이동
  if (trainingSet.status === 'completed') {
    const dateParam = formatDateForUrl(date);
    return `/result-list?sessionId=${trainingSet.sessionId}&type=${trainingSet.type}&date=${dateParam}`;
  }

  // vocal 타입인 경우 특별한 경로 처리
  if (trainingSet.type === 'vocal' && trainingSet.currentItemIndex !== undefined && trainingSet.totalItems) {
    const n = Math.floor(trainingSet.totalItems / 5); // 반복 횟수
    const currentIndex = trainingSet.currentItemIndex;
    let path = '';
    let attempt = 1;

    if (currentIndex >= 0 && currentIndex < n) {
      // 0 ~ n-1: /voice-training/mpt
      path = '/voice-training/mpt';
      attempt = currentIndex + 1;
    } else if (currentIndex >= n && currentIndex < 2 * n) {
      // n ~ 2n-1: /voice-training/crescendo
      path = '/voice-training/crescendo';
      attempt = currentIndex - n + 1;
    } else if (currentIndex >= 2 * n && currentIndex < 3 * n) {
      // 2n ~ 3n-1: /voice-training/decrescendo
      path = '/voice-training/decrescendo';
      attempt = currentIndex - 2 * n + 1;
    } else if (currentIndex >= 3 * n && currentIndex < 4 * n) {
      // 3n ~ 4n-1: /voice-training/loud-soft
      path = '/voice-training/loud-soft';
      attempt = currentIndex - 3 * n + 1;
    } else if (currentIndex >= 4 * n && currentIndex < 5 * n) {
      // 4n ~ 5n-1: /voice-training/soft-loud
      path = '/voice-training/soft-loud';
      attempt = currentIndex - 4 * n + 1;
    } else {
      // 범위를 벗어난 경우 기본 practice 페이지로 이동
      return `/practice?sessionId=${trainingSet.sessionId}&type=${trainingSet.type}&itemIndex=${trainingSet.currentItemIndex}`;
    }

    return `${path}?attempt=${attempt}&sessionId=${trainingSet.sessionId}`;
  }

  // vocal이 아니거나 필요한 정보가 없는 경우 기존 로직 사용
  return `/practice?sessionId=${trainingSet.sessionId}&type=${trainingSet.type}&itemIndex=${trainingSet.currentItemIndex}`;
};

