import React from "react";
import { MessageCircle } from "lucide-react";

// --- FeedbackSummary 컴포넌트 ---
/**
 * 피드백 요약 표시 컴포넌트
 */
interface FeedbackSummaryProps {
  feedback?: string;
}

const FeedbackSummary: React.FC<FeedbackSummaryProps> = ({
  feedback = "전반적으로 좋은 발음입니다. '과' 음절에서 자음을 조금 더 명확하게 발음하시면 더욱 정확해집니다. 입모양과 발성이 안정적이니 꾸준히 연습하시면 됩니다."
}) => {
  return (
    <>
      <section className="w-full self-stretch pt-5 pb-1">
        {/* <div className="mx-auto w-full max-w-6xl rounded-2xl border border-gray-200 bg-white p-4 shadow-lg sm:p-6"> */}
        <div className="pb-3 flex items-center">
          <MessageCircle
            className="w-7 h-7 mr-3 text-green-500"
            strokeWidth={2.5}
          />
          <span className="text-slate-800 text-2xl md:text-3xl font-semibold leading-9">
            한 줄 요약
          </span>
        </div>
        <div className="self-stretch p-4 bg-slate-50 rounded-2xl inline-flex justify-start items-center">
          <div className="flex-1 justify-center text-slate-700 text-2xl font-semibold leading-10">{feedback}</div>
        </div>
        {/* <div className="px-6 bg-slate-50 rounded-2xl">
      <div>
        <p className="text-slate-700 text-lg md:text-2xl font-semibold leading-9">
          {feedback}
        </p>
      </div>
    </div> */}
      </section>
    </>
  );
};

export default FeedbackSummary;
