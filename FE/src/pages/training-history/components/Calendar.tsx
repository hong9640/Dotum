import { Card, CardContent, CardHeader } from "@/components/ui/card";
import CalendarHeader from "./CalendarHeader";
import CalendarGrid from "./CalendarGrid";
import CalendarLegend from "./CalendarLegend";
import { useCalendar } from "@/hooks/useCalendar";

// 훈련 세트 수 데이터 타입
export interface TrainingCountMap {
  [isoDate: string]: number; // "YYYY-MM-DD" -> 세트 수
}

interface CalendarProps {
  counts: TrainingCountMap;
}

export function Calendar({ counts }: CalendarProps) {
  const { year, monthLabel, matrix, goPrev, goNext, setYear } = useCalendar();

  return (
    <Card className="rounded-2xl border-gray-200 shadow-sm w-[932px]">
      <CardHeader className="pb-4">
        <CalendarHeader
          year={year}
          monthLabel={monthLabel}
          onPrev={goPrev}
          onNext={goNext}
          onYearChange={setYear}
        />
      </CardHeader>
      <CardContent className="w-[932px]">
        <CalendarGrid matrix={matrix} counts={counts} />
        <CalendarLegend />
      </CardContent>
    </Card>
  );
}

