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
      <div className="grid grid-cols-7 gap-2 w-[892px]">
        {matrix.map(({ date, inMonth }, idx) => {
          const y = date.getFullYear();
          const m1 = date.getMonth() + 1;
          const d = date.getDate();
          const iso = toISO(y, m1, d);
          const setCnt = counts[iso] ?? 0;

          // 배지 색상 규칙
          const badgeClass = setCnt >= 3 ? "bg-green-500" : setCnt >= 1 ? "bg-green-400" : "";

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
              className={`w-[124px] h-[94px] rounded-xl border border-gray-200 px-[1px] py-[8.5px] flex flex-col items-center gap-[6px] flex-shrink-0 ${
                inMonth ? "bg-white cursor-pointer hover:bg-gray-50 hover:shadow-sm transition-all duration-200" : "bg-gray-50"
              }`}
              onClick={handleDateClick}
            >
              <div className="w-full flex items-center justify-start">
                <span className={`text-lg font-semibold ${
                  inMonth ? numClass : "text-gray-300"
                }`}>
                  {d}
                </span>
              </div>

              {setCnt > 0 && (
                <div className="flex-1 flex items-center justify-center">
                  <div className={`w-[92px] px-2 py-1.5 rounded-xl text-center ${badgeClass}`}>
                    <span className="text-white text-sm font-semibold">
                      {setCnt}회 학습
                    </span>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </>
  );
}

export default CalendarGrid;

