import { Card, CardContent, CardHeader } from "@/shared/components/ui/card";
import CalendarHeader from "./CalendarHeader";
import CalendarGrid from "./CalendarGrid";
import CalendarLegend from "./CalendarLegend";
import { useCalendar } from "@/features/training-history/hooks";
import { useEffect } from "react";

// 연습 세트 수 데이터 타입
export interface TrainingCountMap {
  [isoDate: string]: number; // "YYYY-MM-DD" -> 세트 수
}

interface CalendarProps {
  counts: TrainingCountMap;
  onDateClick?: (date: string) => void;
  onMonthChange?: (year: number, month1Based: number) => void;
}

export function Calendar({ counts, onDateClick, onMonthChange }: CalendarProps) {
  const { year, monthLabel, matrix, goPrev, goNext, setYear, monthIndex0 } = useCalendar();

  useEffect(() => {
    if (onMonthChange) {
      onMonthChange(year, monthIndex0 + 1);
    }
  }, [year, monthIndex0, onMonthChange]);

  return (
    <Card className="rounded-2xl border-gray-200 shadow-sm w-full max-w-[942px] mx-auto">
      <CardHeader className="pt-4 pb-4 sm:pt-8 sm:pb-10 px-4">
        <CalendarHeader
          year={year}
          monthLabel={monthLabel}
          onPrev={goPrev}
          onNext={goNext}
          onYearChange={setYear}
        />
      </CardHeader>
      <CardContent className="w-full px-2.5 sm:px-4 md:px-6">
        <CalendarGrid matrix={matrix} counts={counts} onDateClick={onDateClick} />
        <CalendarLegend />
      </CardContent>
    </Card>
  );
}

