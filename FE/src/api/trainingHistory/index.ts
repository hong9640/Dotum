import { apiClient } from "../axios";

/**
 * 월별 훈련 달력 조회 API 응답 타입
 * - 키: ISO 날짜 문자열 (YYYY-MM-DD)
 * - 값: 해당 날짜의 훈련(세트) 횟수
 */
export type TrainingCalendarMap = Record<string, number>;

/**
 * 월별 훈련 달력 조회
 * GET /train/training-sessions/calendar/{year}/{month}
 *
 * @param year - 연도 (예: 2025)
 * @param month - 월 (1~12)
 * @returns 날짜별 훈련 횟수 맵
 */
export async function getTrainingCalendar(
  year: number,
  month: number
): Promise<TrainingCalendarMap> {
  const response = await apiClient.get<TrainingCalendarMap>(
    `/train/training-sessions/calendar/${year}/${month}`
  );
  return response.data;
}
