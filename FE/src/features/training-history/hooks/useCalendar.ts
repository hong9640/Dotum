import { useState, useMemo } from 'react';

// 유틸: 월 정보 계산
function getMonthMatrix(year: number, monthIndex0: number) {
  // monthIndex0: 0=Jan
  const first = new Date(year, monthIndex0, 1);
  const last = new Date(year, monthIndex0 + 1, 0);
  const daysInMonth = last.getDate();
  const firstWeekday = first.getDay(); // 0=Sun

  // 앞쪽 채움(지난달)
  const prevLast = new Date(year, monthIndex0, 0);
  const prevDays = prevLast.getDate();

  const leading = firstWeekday; // 보여줄 이전달 일수
  const cells: { date: Date; inMonth: boolean }[] = [];

  for (let i = leading - 1; i >= 0; i--) {
    cells.push({ date: new Date(year, monthIndex0 - 1, prevDays - i), inMonth: false });
  }
  for (let d = 1; d <= daysInMonth; d++) {
    cells.push({ date: new Date(year, monthIndex0, d), inMonth: true });
  }
  // 뒤쪽 채움(다음달)
  const trailing = (7 - (cells.length % 7)) % 7;
  for (let d = 1; d <= trailing; d++) {
    cells.push({ date: new Date(year, monthIndex0 + 1, d), inMonth: false });
  }
  return cells;
}

export function useCalendar(
  initialYear: number = new Date().getFullYear(),
  initialMonth: number = new Date().getMonth()
) {
  const [year, setYear] = useState<number>(initialYear);
  const [monthIndex0, setMonthIndex0] = useState<number>(initialMonth); // 0=1월

  const monthFormatter = useMemo(() => new Intl.DateTimeFormat("ko-KR", { month: "long" }), []);
  const monthLabel = useMemo(() => monthFormatter.format(new Date(year, monthIndex0, 1)), [monthFormatter, year, monthIndex0]);
  const matrix = useMemo(() => getMonthMatrix(year, monthIndex0), [year, monthIndex0]);

  const goPrev = () => {
    const d = new Date(year, monthIndex0, 1);
    d.setMonth(d.getMonth() - 1);
    setYear(d.getFullYear());
    setMonthIndex0(d.getMonth());
  };

  const goNext = () => {
    const d = new Date(year, monthIndex0, 1);
    d.setMonth(d.getMonth() + 1);
    setYear(d.getFullYear());
    setMonthIndex0(d.getMonth());
  };

  return {
    year,
    monthIndex0,
    monthLabel,
    matrix,
    goPrev,
    goNext,
    setYear,
  };
}
