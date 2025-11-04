import React from 'react';
import { ChevronLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ResultHeaderProps {
  type: string;
  date: string;
  onBack: () => void;
}

const ResultHeader: React.FC<ResultHeaderProps> = ({ type, date, onBack }) => {
  return (
    <div className="px-8 py-7 relative w-full max-w-7xl mx-auto inline-flex justify-center items-start gap-2.5">
      <div className="w-full h-auto md:h-20 inline-flex flex-col justify-start items-center gap-2.5">
        {/* 제목 */}
        <div className="self-stretch px-4 inline-flex justify-center items-center gap-2.5">
          <h1 className="text-center justify-start text-slate-700 text-2xl md:text-4xl font-bold leading-tight md:leading-[48px]">
            {type === 'word' ? '단어' : '문장'} 훈련 결과
          </h1>
        </div>
        {/* 날짜 */}
        <div className="self-stretch px-4 inline-flex justify-center items-center gap-2.5">
          <p className="text-center justify-start text-slate-500 text-base md:text-xl font-semibold leading-snug md:leading-7">
            {date}
          </p>
        </div>
      </div>
      {/* 홈으로 버튼 */}
      <Button
        variant="ghost"
        className="px-2 md:px-4 py-2 md:py-3.5 left-4 md:left-[32px] top-4 md:top-[30px] absolute rounded-lg flex justify-center items-center gap-2 md:gap-3 group transition-opacity hover:opacity-80"
        onClick={onBack}
      >
        <ChevronLeft className="w-6 h-6 md:w-8 md:h-8 text-slate-500" strokeWidth={3} />
        <span className="justify-start text-slate-500 text-xl md:text-3xl font-normal leading-7 md:leading-9">
          홈으로
        </span>
      </Button>
    </div>
  );
};

export default ResultHeader;
