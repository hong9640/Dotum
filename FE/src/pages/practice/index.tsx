import React, { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useMediaRecorder } from "@/hooks/useMediaRecorder";
import { usePracticeStore } from "@/stores/practiceStore";
import TrainingLayout from "@/pages/practice/components/practice/TrainingLayout";
import PracticeComponent from "@/pages/practice/components/practice/PracticeComponent";
import ResultComponent from "@/pages/result/components/ResultComponent";
import { getCurrentItem, getCurrentItemErrorMessage, type CurrentItemResponse } from "@/api/training-session/currentItem";
import { getTrainingSession, type CreateTrainingSessionResponse } from "@/api/training-session";

const PracticePage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentItem, setCurrentItem] = useState<CurrentItemResponse | null>(null);
  const [sessionData, setSessionDataState] = useState<CreateTrainingSessionResponse | null>(null);
  const [showResult, setShowResult] = useState(false);
  
  // 상태 관리
  const { 
    addRecordedVideo,
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
        console.log('세션 데이터 로드 중...', { sessionId: sessionIdParam, type: sessionTypeParam });
        
        const sessionId = Number(sessionIdParam);
        if (isNaN(sessionId)) {
          setError('세션 ID가 유효하지 않습니다.');
          setIsLoading(false);
          return;
        }
        
        // 세션 정보와 현재 아이템을 병렬로 조회
        const [sessionData, currentItemData] = await Promise.all([
          getTrainingSession(sessionId),
          getCurrentItem(sessionId)
        ]);
        
        setSessionDataState(sessionData);
        setCurrentItem(currentItemData);
        
        // 아이템이 완료된 경우 결과 페이지 표시
        if (currentItemData.is_completed) {
          setShowResult(true);
        } else {
          setShowResult(false);
        }
        
        // 현재 아이템의 단어/문장 설정
        const targetText = currentItemData.word || currentItemData.sentence || '';
        
        // 세션 데이터 설정 (실제 API 데이터 반영)
        setSessionData(sessionIdParam, sessionTypeParam, [targetText], sessionData?.total_items || 10, currentItemData.item_index);
        
        setIsLoading(false);
      } catch (err) {
        console.error('세션 데이터 로드 실패:', err);
        const errorMessage = getCurrentItemErrorMessage(err);
        setError(errorMessage);
        setIsLoading(false);
      }
    };

    loadSessionData();
  }, [sessionIdParam, sessionTypeParam, setSessionData, navigate]);

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

  const handleViewAllResults = () => {
    // 전체 결과 페이지로 이동
    navigate('/result-list');
  };

  const handleViewResults = () => {
    // 녹화 완료 후 결과 페이지 표시 (진행률과 단어는 그대로 유지)
    console.log('🎬 녹화 완료 - 결과 페이지 표시:', {
      currentItemIndex: currentItem?.item_index,
      currentWord: currentItem?.word || currentItem?.sentence,
      progressDisplay: `${(currentItem?.item_index || 0) + 1}/${sessionData?.total_items}`
    });
    
    setShowResult(true);
  };

  const handleNextWord = async () => {
    if (!sessionIdParam || !currentItem?.has_next) return;
    
    const sessionId = Number(sessionIdParam);
    if (isNaN(sessionId)) return;
    
    try {
      // 다음 아이템 조회
      const nextItemData = await getCurrentItem(sessionId);
      
      console.log('다음 아이템 조회 결과:', nextItemData);
      
      setCurrentItem(nextItemData);
      
      // 다음 아이템이 완료된 경우 결과 페이지 표시
      if (nextItemData.is_completed) {
        setShowResult(true);
      } else {
        setShowResult(false);
      }
      
      // 다음 아이템의 단어/문장으로 업데이트
      const targetText = nextItemData.word || nextItemData.sentence || '';
      setSessionData(sessionIdParam, sessionTypeParam!, [targetText], sessionData?.total_items || 10, nextItemData.item_index);
      
      console.log('다음 아이템으로 이동 완료:', {
        itemIndex: nextItemData.item_index,
        targetText,
        hasNext: nextItemData.has_next,
        showResult
      });
    } catch (err) {
      console.error('다음 아이템 로드 실패:', err);
      const errorMessage = getCurrentItemErrorMessage(err);
      setError(errorMessage);
    }
  };

  const handlePreviousWord = async () => {
    if (!sessionIdParam || currentItem?.item_index === 0) return;
    
    const sessionId = Number(sessionIdParam);
    if (isNaN(sessionId)) return;
    
    try {
      // 이전 아이템 조회
      const prevItemData = await getCurrentItem(sessionId);
      
      console.log('이전 아이템 조회 결과:', prevItemData);
      
      setCurrentItem(prevItemData);
      
      // 이전 아이템이 완료된 경우 결과 페이지 표시
      if (prevItemData.is_completed) {
        setShowResult(true);
      } else {
        setShowResult(false);
      }
      
      // 이전 아이템의 단어/문장으로 업데이트
      const targetText = prevItemData.word || prevItemData.sentence || '';
      setSessionData(sessionIdParam, sessionTypeParam!, [targetText], sessionData?.total_items || 10, prevItemData.item_index);
      
      console.log('이전 아이템으로 이동 완료:', {
        itemIndex: prevItemData.item_index,
        targetText,
        hasNext: prevItemData.has_next,
        showResult
      });
    } catch (err) {
      console.error('이전 아이템 로드 실패:', err);
      const errorMessage = getCurrentItemErrorMessage(err);
      setError(errorMessage);
    }
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
  if (!currentItem || !sessionData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-6">
          <Alert>
            <AlertTitle>데이터 없음</AlertTitle>
            <AlertDescription className="mt-2">
              훈련할 데이터가 없습니다.
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
    <TrainingLayout
      currentItem={currentItem}
      sessionData={sessionData}
      onNext={handleNextWord}
      onPrevious={handlePreviousWord}
    >
      {showResult ? (
        <ResultComponent onViewAllResults={handleViewAllResults} />
      ) : (
        <PracticeComponent
          videoRef={videoRef}
          recordingState={recordingState}
          elapsed={elapsed}
          blobUrl={blobUrl}
          permissionError={permissionError}
          onStartRecording={startRecording}
          onStopRecording={stopRecording}
          onRetake={retake}
          onViewResults={handleViewResults}
        />
      )}
    </TrainingLayout>
  );
};

export default PracticePage;