/**
 * 캘린더 스타일 계산 유틸리티 함수
 */

/**
 * 연습 횟수에 따른 배지 스타일 클래스 반환
 */
export const getBadgeClass = (count: number): string => {
  if (count >= 5) return "bg-emerald-600 text-white";
  if (count >= 1) return "bg-emerald-400 text-white";
  return "";
};

/**
 * 연습 횟수에 따른 배지 배경색 클래스 반환
 */
export const getBadgeColor = (count: number): string => {
  if (count >= 5) return "bg-emerald-600";
  if (count >= 1) return "bg-emerald-400";
  return "";
};

/**
 * 요일(day of week)에 따른 숫자 색상 클래스 반환
 * @param dayOfWeek 0=일요일, 6=토요일
 */
export const getDayNumberClass = (dayOfWeek: number, inMonth: boolean): string => {
  if (!inMonth) return "text-gray-300";
  
  if (dayOfWeek === 0) return "text-red-400"; // 일요일
  if (dayOfWeek === 6) return "text-blue-500"; // 토요일
  return "text-slate-600"; // 평일
};

/**
 * 현재 연도 기준으로 선택 가능한 연도 배열 생성
 * @param currentYear 현재 연도
 * @param range 범위 (기본값: 2, 즉 ±2년)
 */
export const getYearOptions = (currentYear: number, range: number = 2): number[] => {
  return Array.from({ length: range * 2 + 1 }, (_, i) => currentYear - range + i);
};

