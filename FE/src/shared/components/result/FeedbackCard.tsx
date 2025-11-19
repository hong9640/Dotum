import React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/shared/components/ui/card";
import { BarChart2 } from "lucide-react";
import PronunciationScore from "./PronunciationScore";
import FeedbackSummary from "./FeedbackSummary";
import DetailedEvaluationItems from "./DetailedEvaluationItems";
import ImprovementPoints from "./ImprovementPoints";
import type { ItemFeedback } from "@/shared/types/result";

/**
 * PraatMetrics 타입 정의 (feature에서 정의된 타입을 참조하지 않도록)
 */
interface PraatData {
  f1?: number | null;
  f2?: number | null;
  cpp?: number | null;
  hnr?: number | null;
  csid?: number | null;
}

interface FeedbackCardComponentProps {
  hideSections?: boolean;
  praatData?: PraatData | null;
  praatLoading?: boolean;
  feedback?: ItemFeedback | null;
  onDetailClick?: () => void; // DetailedEvaluationItems의 자세히 보기 버튼 클릭 핸들러
  showDetailButton?: boolean; // DetailedEvaluationItems의 자세히 보기 버튼 표시 여부
}

/**
 * 발음 평가 피드백 카드 컴포넌트
 * 순수 프레젠테이션 컴포넌트 - props로만 데이터와 콜백을 받습니다.
 */
const FeedbackCard: React.FC<FeedbackCardComponentProps> = ({ 
  hideSections = false, 
  praatData, 
  praatLoading: _praatLoading = false, 
  feedback,
  onDetailClick,
  showDetailButton = true,
}) => {
  const similarity = 87; // 피드백 점수 (예시)

  return (
    <Card className="w-full shadow-lg rounded-2xl">
      <CardHeader className="p-7">
        <CardTitle className="flex items-center text-2xl md:text-3xl font-semibold text-slate-800 pb-2">
          <BarChart2 className="w-7 h-7 mr-3 text-green-500" strokeWidth={2.5} />
          발음 평가 피드백
        </CardTitle>
      </CardHeader>
      <CardContent className="p-7 pt-0">
        <div className="flex flex-col space-y-6">
          {/* 1. 발음 유사도 섹션 */}
          {!hideSections && <PronunciationScore similarity={similarity} />}

          {/* 2. 피드백 요약 섹션(한 줄 요약) */}
          <FeedbackSummary feedback={feedback?.item} />

          {/* 3. 세부 평가 항목 섹션 */}
          <DetailedEvaluationItems 
            praatData={praatData} 
            feedback={feedback}
            onDetailClick={onDetailClick}
            showDetailButton={showDetailButton}
          />

          {/* 4. 개선 포인트 섹션 */}
          {!hideSections && <ImprovementPoints />}
        </div>
      </CardContent>
    </Card>
  );
};

export default FeedbackCard;
export type { FeedbackCardComponentProps };

