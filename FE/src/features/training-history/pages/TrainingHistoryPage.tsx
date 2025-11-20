import React, { useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import { Calendar, type TrainingCountMap } from "../components";
import TrainingDayDetail from "./TrainingHistoryDetailPage";
import { getTrainingCalendar } from "../api";
import { formatDateForUrl, formatDateFromUrl } from "../utils";


export default function TrainingHistoryPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [counts, setCounts] = React.useState<TrainingCountMap>({});

  // URL에서 date 파라미터 읽기
  const dateParam = searchParams.get('date');

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
        onTrainingSetClick={() => {
          // 여기서 상세 모달이나 다른 페이지로 이동할 수 있습니다
        }}
      />
    );
  }

  return (
    <div className="min-h-screen w-full flex flex-col">
      <div className="container flex justify-center mx-auto px-6 xl:px-8 pt-8 pb-0 sm-pb-5 ">
        <div className="px-8 py-7 relative w-full max-w-7xl mx-auto inline-flex justify-center items-start gap-2.5 max-w-[900px]">
          <div className="w-full h-auto md:h-20 inline-flex flex-col justify-start items-center gap-2.5">
            {/* 제목 */}
            <div className="self-stretch px-4 inline-flex justify-center items-center gap-2.5">
              <h1 className="text-center justify-start text-slate-800 text-2xl md:text-4xl font-bold leading-tight md:leading-[48px]">
                연습 기록
              </h1>
            </div>
            {/* 날짜 */}
            <div className="self-stretch px-4 inline-flex justify-center items-center gap-2.5">
              <p className="text-center justify-start text-slate-500 text-base md:text-xl font-semibold leading-snug md:leading-7">
                날짜별 발음 연습 기록을 확인하세요.
              </p>
            </div>
          </div>
        </div>
      </div>
      <main className="container mx-auto px-6 xl:px-8 pb-12 mb:pt-16 flex-1">
        <div className="mx-auto max-w-[942px]">
          <Calendar counts={counts} onDateClick={handleDateClick} onMonthChange={handleMonthChange} />
        </div>
      </main>
    </div>
  );
}
