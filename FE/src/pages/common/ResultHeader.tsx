import React from 'react';
import { useLocation, useSearchParams } from 'react-router-dom';
import { ChevronLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ResultHeaderProps {
  type: string;
  date: string;
  onBack: () => void;
  title?: string; // 커스텀 제목 (제공되면 type 기반 제목 대신 사용)
}

const ResultHeader: React.FC<ResultHeaderProps> = ({ type, date, onBack, title }) => {
  const location = useLocation();
  const [searchParams] = useSearchParams();
  
  // title이 제공되면 title을 사용하고, 없으면 type 기반으로 제목 생성
  // API에서 대문자로 오는 경우를 대비해 소문자로 변환하여 비교
  const typeLower = (type || '').toLowerCase();
  let headerTitle: string;
  
  if (title) {
    headerTitle = title;
  } else if (typeLower === 'word') {
    headerTitle = '단어 연습 결과';
  } else if (typeLower === 'sentence') {
    headerTitle = '문장 연습 결과';
  } else if (typeLower === 'vocal') {
    headerTitle = '발성 연습 결과';
  } else {
    headerTitle = '연습 결과';
  }
  
  // 버튼 텍스트 결정: URL에 date 파라미터가 있거나 result-detail 페이지이면 "돌아가기", 아니면 "홈으로"
  const dateParam = searchParams.get('date');
  const isDetailPage = location.pathname === '/result-detail';
  const backButtonText = dateParam || isDetailPage ? "돌아가기" : "홈으로";
  return (
    <div className="px-0 sm:px-8 pt-0 pb-7 sm:pt-7 relative w-full max-w-7xl mx-auto flex flex-col sm:inline-flex sm:justify-center items-start gap-2.5">
      {/* 돌아가기/홈으로 버튼 - sm 미만일 때는 일반 플로우, sm 이상일 때는 absolute */}
      <Button
        variant="ghost"
        className="px-2 md:px-4 py-2 md:py-3.5 sm:absolute sm:left-4 md:left-[32px] sm:top-4 md:top-[30px] rounded-lg flex justify-center items-center gap-2 md:gap-3 group transition-opacity hover:opacity-80 mb-4 sm:mb-0"
        onClick={onBack}
      >
        <ChevronLeft className="w-6 h-6 md:w-8 md:h-8 text-slate-500" strokeWidth={3} />
        <span className="justify-start text-slate-500 text-xl md:text-3xl font-normal leading-7 md:leading-9">
          {backButtonText}
        </span>
      </Button>
      <div className="w-full h-auto md:h-20 inline-flex flex-col justify-start items-center gap-2.5">
        {/* 제목 */}
        <div className="self-stretch px-4 inline-flex justify-center items-center gap-2.5">
          <h1 className="text-center justify-start text-slate-700 text-2xl md:text-4xl font-bold leading-tight md:leading-[48px]">
            {headerTitle}
          </h1>
        </div>
        {/* 날짜 */}
        <div className="self-stretch px-4 inline-flex justify-center items-center gap-2.5">
          <p className="text-center justify-start text-slate-500 text-base md:text-xl font-semibold leading-snug md:leading-7">
            {date}
          </p>
        </div>
      </div>
    </div>
  );
};

export default ResultHeader;



