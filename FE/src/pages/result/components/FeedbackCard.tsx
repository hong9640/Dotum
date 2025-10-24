import React from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { BarChart, RotateCcw, Activity } from "lucide-react";
import PronunciationScore from "./PronunciationScore";
import FeedbackSummary from "./FeedbackSummary";

// --- FeedbackCard 컴포넌트 (기존) ---
/**
 * 발음 평가 피드백 카드 컴포넌트
 */
const FeedbackCard: React.FC = () => {
  const navigate = useNavigate();
  const similarity = 87; // 피드백 점수 (예시)

  const handleFeedbackDetail = () => {
    navigate("/result-detail");
  };

  const handleRetake = () => {
    navigate("/practice");
  };

  return (
    // 사용자가 요청한 p-7을 CardHeader와 CardContent의 p-7로 구현
    <Card className="w-full shadow-lg rounded-2xl">
      <CardHeader className="p-7">
        <CardTitle className="flex items-center text-2xl md:text-3xl font-semibold text-slate-800 pb-6">
          {/* lucide-react 'BarChart' 아이콘으로 교체 */}
          <BarChart className="w-6 h-6 mr-3 text-green-500" strokeWidth={2.5} />
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
        </div>
      </CardContent>
      {/* 3. 버튼 섹션 */}
      <CardFooter className="flex-col md:flex-row justify-center items-center gap-6 pt-8 border-t border-gray-200 p-7">
        <Button
          variant="default"
          size="lg"
          onClick={handleFeedbackDetail}
          // 사용자가 요청한 text-3xl을 반응형으로 적용
          className="w-full md:w-auto h-auto min-h-10 px-6 py-4 bg-green-500 text-white hover:bg-green-600 rounded-xl text-xl md:text-3xl font-semibold leading-9"
        >
          {/* lucide-react 'Plus' 아이콘으로 교체 */}
          <Activity className="w-8 h-8 mr-2" strokeWidth={3} />
          피드백 상세
        </Button>
        <Button
          variant="outline"
          size="lg"
          onClick={handleRetake}
          className="w-full md:w-auto h-auto min-h-10 px-6 py-4 bg-white text-slate-700 border-slate-200 border-2 hover:bg-slate-100 hover:text-slate-700 rounded-xl text-xl md:text-3xl font-semibold leading-9"
        >
          {/* lucide-react 'RotateCcw' 아이콘으로 교체 */}
          <RotateCcw className="w-8 h-8 mr-2" strokeWidth={2.5} />
          다시 녹화
        </Button>
      </CardFooter>
    </Card>
  );
};

export default FeedbackCard;
