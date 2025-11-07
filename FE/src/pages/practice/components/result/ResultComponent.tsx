import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import ResultVideoDisplay from "./ResultVideoDisplay";
import FeedbackCard from "./FeedbackCard";
import ActionButtons from "./ActionButtons";
import { usePracticeStore } from "@/stores/practiceStore";
import { getTrainingSession, completeTrainingSession, type CreateTrainingSessionResponse } from "@/api/training-session";
import type { PraatMetrics } from "@/api/training-session/praat";

interface ResultComponentProps {
  userVideoUrl?: string;
  compositedVideoUrl?: string;
  isLoadingCompositedVideo?: boolean;
  compositedVideoError?: string | null;
  onNext?: () => void;
  hasNext?: boolean;
  onBack?: () => void; // result-detail 페이지용 돌아가기 핸들러
  onRetake?: () => void; // 다시 녹화 핸들러
  praatData?: PraatMetrics | null;
  praatLoading?: boolean;
}

const ResultComponent: React.FC<ResultComponentProps> = ({
  userVideoUrl,
  compositedVideoUrl,
  isLoadingCompositedVideo = false,
  compositedVideoError,
  onNext,
  hasNext,
  onBack,
  onRetake,
  praatData,
  praatLoading = false,
}) => {
  const navigate = useNavigate();
  const { sessionId } = usePracticeStore();
  const [isCompletingSession, setIsCompletingSession] = useState(false);

  const handleRetake = () => {
    // onRetake prop이 있으면 그것을 사용, 없으면 기본 동작 (navigate)
    if (onRetake) {
      onRetake();
    } else {
      navigate("/practice");
    }
  };

  const handleViewAllResults = async () => {
    if (!sessionId) {
      console.error('세션 ID가 없습니다.');
      alert('세션 정보를 찾을 수 없습니다. 홈페이지에서 다시 시작해주세요.');
      return;
    }

    setIsCompletingSession(true);
    
    let sessionData: CreateTrainingSessionResponse | null = null;
    
    try {
      console.log('전체 결과 보기 처리 시작:', { sessionId });
      
      // 먼저 세션 상태를 확인하여 모든 아이템이 완료되었는지 검증
      sessionData = await getTrainingSession(Number(sessionId));
      console.log('세션 상태 확인:', {
        totalItems: sessionData.total_items,
        completedItems: sessionData.completed_items,
        status: sessionData.status,
        type: sessionData.type
      });
      
      // total_items와 completed_items의 값이 같은지 확인
      if (sessionData.total_items !== sessionData.completed_items) {
        console.warn('아직 모든 아이템이 완료되지 않음:', {
          completed: sessionData.completed_items,
          total: sessionData.total_items
        });
        
        // 같지 않으면 alert 표시 후 함수 종료
        const trainingType = sessionData.type === 'word' ? '단어' : sessionData.type === 'sentence' ? '문장' : '발성';
        alert(`아직 제출하지 않은 ${trainingType} 훈련이 있습니다.`);
        return;
      }
      
      // 두 값이 같으면 세션 종료 API 호출
      await completeTrainingSession(Number(sessionId));
      console.log('훈련 세션 종료 성공');
      
      // 세션 종료 성공 후 result-list 페이지로 이동 (sessionId와 type을 URL 파라미터로 전달)
      const resultListUrl = `/result-list?sessionId=${sessionId}&type=${sessionData.type}`;
      console.log('전체 결과 페이지로 이동:', resultListUrl);
      
      navigate(resultListUrl);
    } catch (error: any) {
      console.error('전체 결과 보기 실패:', error);
      
      // 에러 상태에 따른 처리
      if (error.status === 400) {
        // 400: 아직 모든 아이템이 완료되지 않음
        const trainingType = sessionData?.type === 'word' ? '단어' : sessionData?.type === 'sentence' ? '문장' : '발성';
        alert(`아직 제출하지 않은 ${trainingType} 훈련이 있습니다.`);
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
        const errorMessage = error.message || '세션 종료 중 오류가 발생했습니다.';
        console.error('전체 결과 보기 실패:', errorMessage);
        alert(errorMessage);
      }
    } finally {
      setIsCompletingSession(false);
    }
  };

  return (
    <>
      {/* result-detail 페이지에서는 동영상 부분 주석처리 */}
      {!onBack && (
        <ResultVideoDisplay 
          userVideoUrl={userVideoUrl}
          compositedVideoUrl={compositedVideoUrl}
          isLoadingCompositedVideo={isLoadingCompositedVideo}
          compositedVideoError={compositedVideoError}
        />
      )}
      {/* <ResultVideoDisplay 
        userVideoUrl={userVideoUrl}
        compositedVideoUrl={compositedVideoUrl}
        isLoadingCompositedVideo={isLoadingCompositedVideo}
        compositedVideoError={compositedVideoError}
      /> */}
      <FeedbackCard hideSections={!!onBack} praatData={praatData} praatLoading={praatLoading} />
      <ActionButtons
        onRetake={onBack ? undefined : handleRetake}
        onViewAllResults={onBack ? undefined : handleViewAllResults}
        onNext={onBack ? undefined : onNext}
        hasNext={hasNext}
        isCompletingSession={isCompletingSession}
        onBack={onBack}
      />
    </>
  );
};

export default ResultComponent;
