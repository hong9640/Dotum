import React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { BarChart2 } from "lucide-react";
import PronunciationScore from "./PronunciationScore";
import FeedbackSummary from "./FeedbackSummary";
import DetailedEvaluationItems from "./DetailedEvaluationItems";
import ImprovementPoints from "./ImprovementPoints";

interface FeedbackCardProps {
}

/**
 * 발음 평가 피드백 카드 컴포넌트
 */
const FeedbackCard: React.FC<FeedbackCardProps> = () => {
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
          {/* 1. 발음 유사도 섹션 */}
          <PronunciationScore similarity={similarity} />

          {/* 2. 피드백 요약 섹션 */}
          <FeedbackSummary />

          {/* 3. 세부 평가 항목 섹션 */}
          <DetailedEvaluationItems />

          {/* 4. 개선 포인트 섹션 */}
          <ImprovementPoints />
        </div>
      </CardContent>
    </Card>
  );
};

export default FeedbackCard;
export type { FeedbackCardProps };
