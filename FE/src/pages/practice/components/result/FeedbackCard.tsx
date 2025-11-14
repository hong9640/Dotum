import React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { BarChart2 } from "lucide-react";
import PronunciationScore from "./PronunciationScore";
import FeedbackSummary from "./FeedbackSummary";
import DetailedEvaluationItems from "./DetailedEvaluationItems";
import ImprovementPoints from "./ImprovementPoints";
import type { PraatMetrics } from "@/api/trainingSession/praat";

interface FeedbackCardProps {
  hideSections?: boolean; // result-detail 페이지에서 일부 섹션 숨김
  praatData?: PraatMetrics | null;
  praatLoading?: boolean; // 현재 사용되지 않지만 호환성을 위해 유지
}

/**
 * 발음 평가 피드백 카드 컴포넌트
 */
const FeedbackCard: React.FC<FeedbackCardProps> = ({ hideSections = false, praatData, praatLoading: _praatLoading = false }) => {
  const similarity = 87; // 피드백 점수 (예시)

  return (
    // 사용자가 요청한 p-7을 CardHeader와 CardContent의 p-7로 구현
    <Card className="w-full shadow-lg rounded-2xl">
      <CardHeader className="p-7">
        <CardTitle className="flex items-center text-2xl md:text-3xl font-semibold text-slate-800 pb-2">
          {/* lucide-react 'BarChart' 아이콘으로 교체 */}
          <BarChart2 className="w-7 h-7 mr-3 text-green-500" strokeWidth={2.5} />
          발음 평가 피드백
        </CardTitle>
      </CardHeader>
      {/* CardContent에 p-7을 적용하고, 상단 패딩은 0으로 설정 */}
      <CardContent className="p-7 pt-0">
        <div className="flex flex-col space-y-6">
          {/* 1. 발음 유사도 섹션 - result-detail 페이지에서 주석처리 */}
          {/* <PronunciationScore similarity={similarity} /> */}
          {!hideSections && <PronunciationScore similarity={similarity} />}

          {/* 2. 피드백 요약 섹션(한 줄 요약) - result-detail 페이지에서 주석처리 */}
          {/* <FeedbackSummary /> */}
          {!hideSections && <FeedbackSummary />}

          {/* 3. 세부 평가 항목 섹션 */}
          <DetailedEvaluationItems praatData={praatData} />

          {/* 4. 개선 포인트 섹션 - result-detail 페이지에서 주석처리 */}
          {/* <ImprovementPoints /> */}
          {!hideSections && <ImprovementPoints />}
        </div>
      </CardContent>
    </Card>
  );
};

export default FeedbackCard;
export type { FeedbackCardProps };
