import React, { useState, useCallback } from "react";
import { Calendar } from "./components/Calendar";
import TrainingDayDetail from "../training-history-detail";
import { getTrainingCalendar } from "@/api/training-history";

// 훈련 세트 수 데이터 타입
interface TrainingCountMap {
  [isoDate: string]: number; // "YYYY-MM-DD" -> 세트 수
}


export default function TrainingHistoryPage() {
  const [counts, setCounts] = React.useState<TrainingCountMap>({});
  const [selectedDate, setSelectedDate] = useState<string | null>(null);

  const handleDateClick = (date: string) => {
    setSelectedDate(date);
  };

  const handleBack = () => {
    setSelectedDate(null);
  };

  const handleMonthChange = useCallback(async (year: number, month1Based: number) => {
    try {
      const data = await getTrainingCalendar(year, month1Based);
      setCounts(data ?? {});
    } catch (e) {
      console.error("Failed to load training calendar", e);
      setCounts({});
    }
  }, []);

  // 날짜 상세 페이지가 선택된 경우
  if (selectedDate) {
    return (
      <TrainingDayDetail 
        date={selectedDate} 
        trainingSets={undefined} // API에서 받아올 데이터
        onBack={handleBack}
        onTrainingSetClick={(trainingSet: any) => {
          console.log('Training set clicked:', trainingSet);
          // 여기서 상세 모달이나 다른 페이지로 이동할 수 있습니다
        }}
      />
    );
  }

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

          <Calendar counts={counts} onDateClick={handleDateClick} onMonthChange={handleMonthChange} />
        </div>
      </main>
    </div>
  );
}
