import React from "react";
import { Calendar } from "./components/Calendar";

// 훈련 세트 수 데이터 타입
interface TrainingCountMap {
  [isoDate: string]: number; // "YYYY-MM-DD" -> 세트 수
}

// 샘플 데이터: 2025-01 (요구 예시 반영)
const SAMPLE_COUNTS: TrainingCountMap = {
  "2025-01-01": 3,
  "2025-01-12": 4,
  "2025-01-16": 1,
  "2025-01-23": 2,
};

export default function TrainingHistoryPage() {
  const [counts] = React.useState<TrainingCountMap>(SAMPLE_COUNTS);

  return (
    <div className="min-h-screen w-full bg-slate-50 flex flex-col">
      <main className="container mx-auto px-6 xl:px-8 py-12 md:py-16 flex-1">
        <div className="mx-auto max-w-[896px]">
          <div className="mb-8">
            <h1 className="text-3xl md:text-4xl font-semibold text-gray-900">훈련 기록</h1>
            <p className="mt-2 text-lg md:text-xl font-medium text-gray-600">
              날짜별 발음 훈련 기록을 확인하세요.
            </p>
          </div>

          <Calendar counts={counts} />
        </div>
      </main>
    </div>
  );
}
