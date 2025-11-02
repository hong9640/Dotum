import React, { useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import { Calendar } from "./components/Calendar";
import TrainingDayDetail from "../training-history-detail";
import { getTrainingCalendar } from "@/api/training-history";

// 훈련 세트 수 데이터 타입
interface TrainingCountMap {
  [isoDate: string]: number; // "YYYY-MM-DD" -> 세트 수
}


export default function TrainingHistoryPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [counts, setCounts] = React.useState<TrainingCountMap>({});
  
  // URL에서 date 파라미터 읽기
  const dateParam = searchParams.get('date');
  
  // 날짜 형식 변환: YYYY-MM-DD -> YYYYMMDD 또는 그 반대
  const formatDateForUrl = (date: string): string => {
    // YYYY-MM-DD 형식이면 YYYYMMDD로 변환
    if (date.includes('-')) {
      return date.replace(/-/g, '');
    }
    return date;
  };
  
  const formatDateFromUrl = (dateStr: string): string => {
    // YYYYMMDD 형식이면 YYYY-MM-DD로 변환
    if (dateStr.length === 8 && !dateStr.includes('-')) {
      return `${dateStr.slice(0, 4)}-${dateStr.slice(4, 6)}-${dateStr.slice(6, 8)}`;
    }
    return dateStr;
  };

  const handleDateClick = (date: string) => {
    // 날짜를 YYYYMMDD 형식으로 변환하여 URL에 추가
    const urlDate = formatDateForUrl(date);
    setSearchParams({ date: urlDate });
  };

  const handleBack = () => {
    // URL에서 date 파라미터 제거
    setSearchParams({});
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

  // 날짜 상세 페이지가 선택된 경우 (URL에 date 파라미터가 있는 경우)
  if (dateParam) {
    const formattedDate = formatDateFromUrl(dateParam);
    return (
      <TrainingDayDetail 
        date={formattedDate} 
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
