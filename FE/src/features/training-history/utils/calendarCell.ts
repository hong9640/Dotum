/**
 * 캘린더 셀 관련 계산 유틸리티
 */
import { dateToISO } from "./calendar";
import { getBadgeClass, getBadgeColor, getDayNumberClass } from "./calendarStyles";

export interface CalendarCellData {
  iso: string;
  day: number;
  setCnt: number;
  badgeClass: string;
  badgeColor: string;
  numClass: string;
  containerClass: string;
}

/**
 * 날짜 셀에 필요한 모든 데이터를 계산하여 반환
 */
export const calculateCellData = (
  date: Date,
  inMonth: boolean,
  counts: Record<string, number>
): CalendarCellData => {
  const iso = dateToISO(date);
  const setCnt = counts[iso] ?? 0;
  const day = date.getDate();
  const dayOfWeek = date.getDay();

  // 스타일 계산
  const badgeClass = getBadgeClass(setCnt);
  const badgeColor = getBadgeColor(setCnt);
  const numClass = getDayNumberClass(dayOfWeek, inMonth);

  // 컨테이너 클래스 계산
  const containerClass = `
    aspect-[124/94] rounded-lg sm:border sm:border-gray-200 border-0
    flex flex-col items-center justify-start
    py-[4px] px-0 sm:p-[6px] md:p-[8px]
    transition-all duration-200
    ${inMonth
      ? "bg-white cursor-pointer hover:bg-slate-50 hover:shadow-sm transition-all duration-200"
      : "sm:bg-slate-50 bg-transparent"
    }`.trim().replace(/\s+/g, ' ');

  return {
    iso,
    day,
    setCnt,
    badgeClass,
    badgeColor,
    numClass,
    containerClass,
  };
};

