import React, { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useMediaRecorder } from "@/hooks/useMediaRecorder";
import { usePracticeStore } from "@/stores/practiceStore";
import ProgressHeader from "@/components/ProgressHeader";
import WordDisplay from "@/components/WordDisplay";
import RecordingPreview from "@/pages/practice/components/RecordingPreview";
import RecordingControls from "@/pages/practice/components/RecordingControls";
import RecordingTips from "@/pages/practice/components/RecordingTips";
import { createTrainingSession, type CreateTrainingSessionResponse } from "@/api/training-session";

const PracticePage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // 상태 관리
  const { 
    currentStep, 
    totalSteps, 
    currentWord, 
    currentWordIndex,
    words,
    sessionId,
    sessionType,
    addRecordedVideo,
    goToNextWord,
    goToPreviousWord,
    setSessionData
  } = usePracticeStore();

  // URL 파라미터에서 세션 정보 가져오기
  const sessionIdParam = searchParams.get('sessionId');
  const sessionTypeParam = searchParams.get('type') as 'word' | 'sentence' | null;

  // 세션 데이터 로드
  useEffect(() => {
    const loadSessionData = async () => {
      if (!sessionIdParam || !sessionTypeParam) {
        setError('세션 정보가 없습니다. 홈페이지에서 다시 시작해주세요.');
        setIsLoading(false);
        return;
      }

      try {
        // 세션 ID로 세션 정보 조회 (현재는 세션 생성 API를 사용)
        // TODO: 실제로는 세션 조회 API를 사용해야 함
        console.log('세션 데이터 로드 중...', { sessionId: sessionIdParam, type: sessionTypeParam });
        
        // 임시로 하드코딩된 데이터 사용 (실제로는 서버에서 받아와야 함)
        const mockWords = sessionTypeParam === 'word' 
          ? ['사과', '바나나', '딸기', '포도', '오렌지', '수박', '참외', '복숭아', '자두', '체리']
          : ['안녕하세요', '좋은 아침입니다', '감사합니다', '죄송합니다', '괜찮습니다', '도움이 필요해요', '이해했습니다', '다시 말씀해주세요', '천천히 말해주세요', '잘 들었습니다'];
        
        // 세션 데이터 설정
        setSessionData(sessionIdParam, sessionTypeParam, mockWords);
        setIsLoading(false);
      } catch (err) {
        console.error('세션 데이터 로드 실패:', err);
        setError('세션 데이터를 불러오는데 실패했습니다.');
        setIsLoading(false);
      }
    };

    loadSessionData();
  }, [sessionIdParam, sessionTypeParam, setSessionData]);

  const handleSave = (file: File, blobUrl: string) => {
    console.log("Saved:", file);
    // 녹화된 비디오를 상태에 추가
    addRecordedVideo(blobUrl);
    // TODO: 업로드 API 연동 (presigned URL or multipart)
  };

  const {
    videoRef,
    recordingState,
    permissionError,
    elapsed,
    blobUrl,
    startRecording,
    stopRecording,
    retake,
  } = useMediaRecorder({ onSave: handleSave });

  const handleViewResults = () => {
    // 녹화 완료 후 결과 페이지로 이동
    navigate('/result');
  };

  const handleNextWord = () => {
    // 다음 단어로 이동
    goToNextWord();
  };

  const handlePreviousWord = () => {
    // 이전 단어로 이동
    goToPreviousWord();
  };

  // 로딩 상태
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-lg text-gray-600">세션 데이터를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  // 에러 상태
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-6">
          <Alert variant="destructive">
            <AlertTitle>오류 발생</AlertTitle>
            <AlertDescription className="mt-2">
              {error}
            </AlertDescription>
          </Alert>
          <button 
            onClick={() => navigate('/')}
            className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            홈으로 돌아가기
          </button>
        </div>
      </div>
    );
  }

  // 데이터가 없는 경우
  if (totalSteps === 0 || words.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-6">
          <Alert>
            <AlertTitle>데이터 없음</AlertTitle>
            <AlertDescription className="mt-2">
              훈련할 {sessionType === 'word' ? '단어' : '문장'}가 없습니다.
            </AlertDescription>
          </Alert>
          <button 
            onClick={() => navigate('/')}
            className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            홈으로 돌아가기
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="min-h-[1105px] px-8 sm:px-12 md:px-24 lg:px-32 py-6 flex justify-center items-start">
        <div className="w-full max-w-[1152px] flex flex-col gap-8">
          {/* 진행률 헤더 */}
          <ProgressHeader step={currentStep} totalSteps={totalSteps} />

          {/* 발음할 단어 표시 */}
          <WordDisplay 
            targetWord={currentWord}
            onNext={handleNextWord}
            onPrevious={handlePreviousWord}
            showNext={currentWordIndex < totalSteps - 1}
            showPrevious={currentWordIndex > 0}
          />

          {/* 녹화 미리보기 */}
          <RecordingPreview
            videoRef={videoRef}
            recordingState={recordingState}
            elapsed={elapsed}
            blobUrl={blobUrl}
          />

          {/* 녹화 컨트롤 */}
          <RecordingControls
            recordingState={recordingState}
            blobUrl={blobUrl}
            onStartRecording={startRecording}
            onStopRecording={stopRecording}
            onRetake={retake}
            onViewResults={handleViewResults}
          />

          {/* 녹화 팁 */}
          <RecordingTips />

          {/* 권한/오류 안내 */}
          {permissionError && (
            <Alert variant="destructive" className="max-w-[896px] mx-auto">
              <AlertTitle>카메라/마이크 접근 실패</AlertTitle>
              <AlertDescription>
                {permissionError} <br />
                브라우저 주소창의 카메라/마이크 아이콘을 눌러 권한을 허용하거나, 다른 브라우저에서 시도해보세요.
              </AlertDescription>
            </Alert>
          )}
        </div>
      </div>
    </div>
  );
};

export default PracticePage;