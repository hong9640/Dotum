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
    <section className="w-full self-stretch pt-5 pb-1">
      <div className="pb-3 flex items-center">
        <MessageCircle
          className="w-7 h-7 mr-3 text-green-500"
          strokeWidth={2.5}
        />
        <span className="text-slate-800 text-2xl md:text-3xl font-semibold leading-9">
          한 줄 요약
        </span>
      </div>
      <div className="self-stretch p-4 bg-slate-50 rounded-2xl inline-flex justify-center items-center min-h-[80px]">
        {feedback ? (
          <div className="flex-1 justify-center text-slate-700 text-xl md:text-2xl font-semibold leading-10">{feedback}</div>
        ) : (
          <Loader2 className="w-8 h-8 text-blue-500 animate-spin" strokeWidth={2} />
        )}
      </div>
    </section>
  );
};

export default FeedbackSummary;
export type { FeedbackSummaryProps };

