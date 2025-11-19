import React from "react";
import { MessageCircle, Loader2 } from "lucide-react";
import type { FeedbackSummaryProps } from "@/shared/types/result";

/**
 * 피드백 요약 표시 컴포넌트
 * 순수 프레젠테이션 컴포넌트 - props로만 데이터를 받습니다.
 */
const FeedbackSummary: React.FC<FeedbackSummaryProps> = ({
  feedback
}) => {
  return (
    <div className="self-stretch px-7 py-8 rounded-2xl shadow-[0px_1px_2px_-1px_rgba(0,0,0,0.10)] shadow-[0px_1px_3px_0px_rgba(0,0,0,0.10)] border-t border-slate-200 flex flex-col gap-6">
      {/* 제목 섹션 */}
      <div className="self-stretch flex justify-start items-start">
        <div className="flex-1 h-6 flex justify-start items-center">
          <div className="pr-3 flex justify-start items-start">
            <div className="self-stretch flex justify-start items-center">
              <MessageCircle
                className="w-7 h-7 text-green-500"
                strokeWidth={2.5}
              />
            </div>
          </div>
          <div className="text-slate-800 text-2xl md:text-3xl font-semibold leading-9">
            한 줄 요약
          </div>
        </div>
      </div>
      <div className="self-stretch p-6 bg-slate-50 rounded-2xl inline-flex justify-center items-center min-h-[80px]">
        {feedback ? (
          <div className="flex-1 justify-center text-slate-700 text-xl md:text-2xl font-semibold leading-10">{feedback}</div>
        ) : (
          <Loader2 className="w-8 h-8 text-blue-500 animate-spin" strokeWidth={2} />
        )}
      </div>
    </div>
  );
};

export default FeedbackSummary;
export type { FeedbackSummaryProps };

