// 훈련 세트 수 데이터 타입
export interface TrainingCountMap {
  [isoDate: string]: number; // "YYYY-MM-DD" -> 세트 수
}

// 유틸: 날짜 포맷
const pad2 = (n: number) => String(n).padStart(2, "0");
const toISO = (y: number, m1: number, d: number) => `${y}-${pad2(m1)}-${pad2(d)}`;

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
    <>
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
          const y = date.getFullYear();
          const m1 = date.getMonth() + 1;
          const d = date.getDate();
          const iso = toISO(y, m1, d);
          const setCnt = counts[iso] ?? 0;

          // 배지 색상 규칙
          const badgeClass = setCnt >= 5 ? "bg-emerald-600 text-white" : setCnt >= 1 ? "bg-emerald-400 text-white" : "";
          const badgeColor = setCnt >= 5 ? "bg-emerald-600" : setCnt >= 1 ? "bg-emerald-400" : "";

          // 주말 색상
          const dow = date.getDay();
          const numClass = dow === 0 ? "text-red-400" : dow === 6 ? "text-blue-500" : "text-slate-600";

          const handleDateClick = () => {
            if (onDateClick && inMonth) {
              onDateClick(iso);
            }
          };

          return (
            <div
              key={iso + idx}
              className={`
                aspect-[124/94] rounded-lg sm:border sm:border-gray-200 border-0
                flex flex-col items-center justify-start
                py-[4px] px-0 sm:p-[6px] md:p-[8px]
                transition-all duration-200
                ${inMonth
                  ? "bg-white cursor-pointer hover:bg-slate-50 hover:shadow-sm transition-all duration-200"
                  : "sm:bg-slate-50 bg-transparent"
                }`}
              onClick={handleDateClick}
            >
              {/* <div
              key={iso + idx}
              className={`
                aspect-square rounded-xl border border-gray-200 
                px-[8.5px] py-[8.5px] 
                flex flex-col items-center justify-start 
                p-[6px] sm:p-[8px] md:p-[10px]
                ${inMonth
                  ? "bg-white cursor-pointer hover:bg-slate-50 hover:shadow-sm transition-all duration-200"
                  : "bg-slate-50"
                }`}
              onClick={handleDateClick}
            > */}
              {/* <div className="w-full flex items-start justify-start"> */}
              <div className="w-full flex items-center justify-center sm:justify-start relative">
                <span
                  className={`font-semibold text-lg sm:text-base md:text-lg ${inMonth ? numClass : "text-gray-300"
                    }`}>
                  {d}
                </span>
                {setCnt > 0 && (
                  <span className={`sm:hidden absolute top-0.5 right-0 h-1.5 w-1.5 rounded-full ${badgeColor}`} />
                )}
              </div>

              <div className="w-full flex-1 flex items-center justify-center">
                <div
                  className={`hidden sm:flex justify-center w-full px-2 py-1.5 rounded-2xl text-center items-center h-8 md:h-9 ${
                    setCnt > 0 ? badgeClass : "invisible"
                  }`}
                >
                  <span className="flex lg:hidden text-[16px] font-semibold">
                {/* <div className="flex-1 flex items-center justify-center w-full">
                  <div className={`hidden sm:flex w-full rounded-xl text-center ${badgeClass} items-center justify-center`}>
                    <span className="text-white text-[10px] sm:text-xs md:text-sm font-semibold text-center"> */}
                      {setCnt}회
                    </span>
                  <span className="hidden lg:flex text-[16px] font-semibold">
                {/* <div className="flex-1 flex items-center justify-center w-full">
                  <div className={`hidden sm:flex w-full rounded-xl text-center ${badgeClass} items-center justify-center`}>
                    <span className="text-white text-[10px] sm:text-xs md:text-sm font-semibold text-center"> */}
                      {setCnt}회 연습
                    </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </>
  );
}

export default CalendarGrid;

