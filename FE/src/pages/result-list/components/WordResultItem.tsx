import React from 'react';
import { ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { WordResult } from "@/types/result-list";

interface WordResultItemProps {
  result: WordResult;
  onDetailClick: (result: WordResult) => void;
}

// 점수에 따른 스타일 반환 헬퍼 함수 - 점수 표시 숨김으로 인해 사용 안 함
// const getScoreStyles = (score: number): string => {
//   if (score >= 90) {
//     // 90점 이상: high (green)
//     return "bg-green-100/50 outline-green-300 text-green-500";
//   }
//   if (score >= 80) {
//     // 80점 이상: medium (blue)
//     return "bg-blue-100/50 outline-blue-300 text-blue-600";
//   }
//   // 80점 미만: low (amber/yellow)
//   return "bg-amber-100/50 outline-amber-300 text-amber-500";
// };

const WordResultItem: React.FC<WordResultItemProps> = ({ result, onDetailClick }) => {
  return (
    <div className="w-full max-w-[1166.40px] px-4 md:px-6 py-4 md:py-6 bg-white rounded-2xl shadow-[0px_1px_2px_-1px_rgba(34,197,94,0.10)] shadow-[0px_1px_3px_0px_rgba(34,197,94,0.10)] outline outline-[1.60px] outline-offset-[-1.60px] outline-gray-200 flex flex-col justify-start items-start">
      <div className="self-stretch min-h-20 inline-flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div className="flex-1 flex justify-start items-start gap-4">
          <div className="w-10 h-10 md:w-12 md:h-12 bg-gradient-to-br from-green-300 to-green-500 rounded-full flex justify-center items-center flex-shrink-0">
            <div className="justify-start text-white text-xl md:text-2xl font-semibold leading-snug md:leading-8">
              {result.id}
            </div>
          </div>
          <div className="flex-1 inline-flex flex-col justify-start items-start gap-2">
            <div className="self-stretch inline-flex justify-start items-center gap-2.5">
              <h3 className="justify-start text-slate-800 text-2xl md:text-3xl font-semibold leading-tight md:leading-9">
                {result.word}
              </h3>
            </div>
            {/* 피드백 정보 - 숨김 처리 */}
            {/* <div className="self-stretch pr-5 inline-flex justify-start items-center gap-2.5">
              <p className="flex-1 justify-start text-slate-500 text-base md:text-xl font-semibold leading-snug md:leading-7">
                {result.feedback}
              </p>
            </div> */}
          </div>
        </div>
        <div className="h-14 flex justify-end sm:justify-start items-center gap-3 w-full sm:w-auto pl-14 sm:pl-0">
          {/* 점수 표시 - 숨김 처리 */}
          {/* <div className={`px-4 md:px-6 py-2 md:py-3 rounded-xl outline outline-[1.50px] outline-offset-[-1.50px] flex justify-center items-center gap-1 overflow-hidden ${getScoreStyles(result.score)}`}>
            <div className="text-xl md:text-2xl font-semibold leading-snug md:leading-8">
              {result.score}점
            </div>
          </div> */}
          <Button
            variant="ghost"
            className="px-2.5 py-[3px] rounded-lg flex justify-start items-center gap-1.5 group transition-opacity hover:opacity-80"
            onClick={() => onDetailClick(result)}
          >
            <span className="justify-start text-slate-600 text-base md:text-xl font-semibold leading-snug md:leading-7">
              자세히
            </span>
            <ChevronRight className="w-4 h-4 md:w-5 md:h-5 text-slate-600" strokeWidth={2.5} />
          </Button>
        </div>
      </div>
    </div>
  );
};

export default WordResultItem;
