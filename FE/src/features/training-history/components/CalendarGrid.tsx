import type { TrainingCountMap } from "./Calendar";
import { calculateCellData } from "../utils";
import CalendarCell from "./CalendarCell";

const WEEKDAYS = [
  { key: "sun", label: "일", className: "text-red-400" },
  { key: "mon", label: "월", className: "text-gray-600" },
  { key: "tue", label: "화", className: "text-gray-600" },
  { key: "wed", label: "수", className: "text-gray-600" },
  { key: "thu", label: "목", className: "text-gray-600" },
  { key: "fri", label: "금", className: "text-gray-600" },
  { key: "sat", label: "토", className: "text-blue-500" },
];

interface CalendarGridProps {
  matrix: { date: Date; inMonth: boolean }[];
  counts: TrainingCountMap;
  onDateClick?: (date: string) => void;
}

function CalendarGrid({ matrix, counts, onDateClick }: CalendarGridProps) {
  return (
    <div className="w-full">
      {/* 요일 헤더 */}
      <div className="grid grid-cols-7 gap-2 pb-2">
        {WEEKDAYS.map((w) => (
          <div key={w.key} className="h-10 flex items-center justify-center">
            <span className={`text-xl md:text-2xl font-semibold ${w.className}`}>
              {w.label}
            </span>
          </div>
        ))}
      </div>

      {/* 날짜 그리드 */}
      <div className="grid grid-cols-7 gap-[2px] sm:gap-1 md:gap-2 w-full max-w-full overflow-hidden">
        {matrix.map(({ date, inMonth }, idx) => {
          const cellData = calculateCellData(date, inMonth, counts);
          return (
            <CalendarCell
              key={cellData.iso + idx}
              cellData={cellData}
              inMonth={inMonth}
              onDateClick={onDateClick}
            />
          );
        })}
      </div>
    </div>
  );
}

export default CalendarGrid;

