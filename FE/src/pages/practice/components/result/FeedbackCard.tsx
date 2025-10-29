import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { BarChart, RotateCcw, ListChecks, ArrowRight, Loader2 } from "lucide-react";
import PronunciationScore from "./PronunciationScore";
import FeedbackSummary from "./FeedbackSummary";
import { usePracticeStore } from "@/stores/practiceStore";
import { completeTrainingSession } from "@/api/training-session";

interface FeedbackCardProps {
  onViewAllResults?: () => void;
}

// --- FeedbackCard 컴포넌트 (기존) ---
/**
 * 발음 평가 피드백 카드 컴포넌트
 */
const FeedbackCard: React.FC<FeedbackCardProps> = ({ onViewAllResults }) => {
  const navigate = useNavigate();
  const { currentWordIndex, totalSteps, goToNextWord, sessionId } = usePracticeStore();
  const [isCompletingSession, setIsCompletingSession] = useState(false);
  const similarity = 87; // 피드백 점수 (예시)

  const handleRetake = () => {
    navigate("/practice");
  };

  const handleViewAllResults = async () => {
    if (!sessionId) {
      console.error('세션 ID가 없습니다.');
      alert('세션 정보를 찾을 수 없습니다. 홈페이지에서 다시 시작해주세요.');
      return;
    }

    setIsCompletingSession(true);
    
    try {
      console.log('훈련 세션 완료 처리 시작:', { sessionId });
      
      // 훈련 세션 완료 API 호출
      const completedSession = await completeTrainingSession(Number(sessionId));
      
      console.log('훈련 세션 완료 성공:', completedSession);
      
      // 완료 후 전체 결과 페이지로 이동
      if (onViewAllResults) {
        onViewAllResults();
      } else {
        navigate("/result-list");
      }
    } catch (error: any) {
      console.error('훈련 세션 완료 실패:', error);
      
      // 에러 상태에 따른 처리
      if (error.status === 400) {
        // 400: 아직 모든 아이템이 완료되지 않음
        alert('아직 모든 아이템이 완료되지 않았습니다. 모든 단어/문장을 완료한 후 다시 시도해주세요.');
      } else if (error.status === 401) {
        // 401: 인증 필요
        alert('인증이 필요합니다. 다시 로그인해주세요.');
        navigate('/login');
        return;
      } else if (error.status === 404) {
        // 404: 세션을 찾을 수 없음
        alert('세션을 찾을 수 없습니다. 홈페이지에서 다시 시작해주세요.');
        navigate('/');
        return;
      } else {
        // 기타 에러
        const errorMessage = error.message || '훈련 세션 완료 중 오류가 발생했습니다.';
        alert(errorMessage);
      }
      
      // 에러가 발생해도 전체 결과 페이지로 이동 (사용자 경험을 위해)
      // 단, 인증 에러나 세션 없음 에러는 제외
      if (error.status !== 401 && error.status !== 404) {
        if (onViewAllResults) {
          onViewAllResults();
        } else {
          navigate("/result-list");
        }
      }
    } finally {
      setIsCompletingSession(false);
    }
  };

  const handleNextWord = () => {
    goToNextWord();
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
      <CardFooter className="flex flex-col md:flex-row md:flex-wrap justify-center items-center gap-6 pt-8 border-t border-gray-200 p-7">
        {/* 다시 녹화 버튼 - 항상 표시 */}
        <Button
          variant="outline"
          size="lg"
          onClick={handleRetake}
          className="w-full md:w-auto h-auto min-h-10 px-6 py-4 bg-white text-slate-700 border-slate-200 border-2 hover:bg-slate-100 hover:text-slate-700 rounded-xl text-xl md:text-3xl font-semibold leading-9"
        >
          <RotateCcw className="w-8 h-8 mr-2" strokeWidth={2.5} />
          다시 녹화
        </Button>
        
        {/* 마지막 단어인 경우: 전체 결과 보기 버튼 표시 */}
        {currentWordIndex === totalSteps - 1 ? (
          <Button
            variant="default"
            size="lg"
            onClick={handleViewAllResults}
            disabled={isCompletingSession}
            className="w-full md:w-auto h-auto min-h-10 px-6 py-4 bg-blue-500 text-white hover:bg-blue-600 disabled:bg-blue-300 disabled:cursor-not-allowed rounded-xl text-xl md:text-3xl font-semibold leading-9"
          >
            {isCompletingSession ? (
              <>
                <Loader2 className="w-8 h-8 mr-2 animate-spin" strokeWidth={3} />
                세션 완료 중...
              </>
            ) : (
              <>
                <ListChecks className="w-8 h-8 mr-2" strokeWidth={3} />
                전체 결과 보기
              </>
            )}
          </Button>
        ) : (
          /* 1~9번째 아이템인 경우: 다음으로 버튼 표시 */
          <Button
            variant="default"
            size="lg"
            onClick={handleNextWord}
            className="w-full md:w-auto h-auto min-h-10 px-6 py-4 bg-green-500 text-white hover:bg-green-600 rounded-xl text-xl md:text-3xl font-semibold leading-9"
          >
            <ArrowRight className="w-8 h-8 mr-2" strokeWidth={3} />
            다음으로
          </Button>
        )}
      </CardFooter>
    </Card>
  );
};

export default FeedbackCard;
export type { FeedbackCardProps };
