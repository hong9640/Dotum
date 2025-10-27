import React from "react";
import { CheckCircle } from "lucide-react";

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
    <div className="px-6 py-7 bg-slate-50 rounded-2xl">
      <div className="pb-6 flex items-center">
        <CheckCircle
          className="w-6 h-6 mr-3 text-green-500"
          strokeWidth={2.5}
        />
        <span className="text-slate-800 text-2xl md:text-3xl font-semibold leading-9">
          피드백 요약
        </span>
      </div>
      <div>
        <p className="text-slate-700 text-lg md:text-2xl font-semibold leading-9">
          {feedback}
        </p>
      </div>
    </div>
  );
};

export default FeedbackSummary;
