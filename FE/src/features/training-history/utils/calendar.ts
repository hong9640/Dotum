/**
 * 캘린더 관련 날짜 유틸리티 함수
 */

/**
 * 숫자를 2자리 문자열로 변환 (앞에 0 패딩)
 */
export const pad2 = (n: number): string => String(n).padStart(2, "0");

/**
 * 날짜를 ISO 형식 문자열로 변환 (YYYY-MM-DD)
 */
export const toISO = (y: number, m1: number, d: number): string => 
  `${y}-${pad2(m1)}-${pad2(d)}`;

/**
 * 날짜 형식 변환: YYYY-MM-DD -> YYYYMMDD
 */
export const formatDateForUrl = (date: string): string => {
  if (date.includes('-')) {
    return date.replace(/-/g, '');
  }
  return date;
};

/**
 * 날짜 형식 변환: YYYYMMDD -> YYYY-MM-DD
 */
export const formatDateFromUrl = (dateStr: string): string => {
  if (dateStr.length === 8 && !dateStr.includes('-')) {
    return `${dateStr.slice(0, 4)}-${dateStr.slice(4, 6)}-${dateStr.slice(6, 8)}`;
  }
  return dateStr;
};

/**
 * Date 객체에서 ISO 형식 문자열 추출
 */
export const dateToISO = (date: Date): string => {
  const y = date.getFullYear();
  const m1 = date.getMonth() + 1;
  const d = date.getDate();
  return toISO(y, m1, d);
};

