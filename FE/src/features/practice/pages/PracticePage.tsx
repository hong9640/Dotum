import React from "react";
import { useNavigate } from "react-router-dom";
import { Alert, AlertDescription, AlertTitle } from "@/shared/components/ui/alert";
import { useMediaRecorder, usePracticePage } from "@/features/practice/hooks";
import TrainingLayout from "@/features/practice/components/TrainingLayout";
import PracticeComponent from "@/features/practice/components/practice/PracticeComponent";
import { Loader2 } from "lucide-react";

const PracticePage: React.FC = () => {
  const navigate = useNavigate();
  
  // 모든 비즈니스 로직을 훅으로 분리
  const {
    isLoading,
    error,
    currentItem,
    sessionData,
    uploadState,
    isCompletingSession,
    sessionIdParam,
    sessionTypeParam,
    handleSave,
    handleRetake: handleRetakeFromHook,
    handleUpload,
    handleNextWord,
    handlePreviousWord,
  } = usePracticePage();

  const {
    recordingState,
    permissionError,
    elapsed,
    blobUrl,
    videoRef,
    isCameraReady,
    startRecording,
    stopRecording,
    retake,
  } = useMediaRecorder({ onSave: handleSave });

  const handleRetake = () => {
    retake();
    handleRetakeFromHook();
  };

  // 로딩 상태
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
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
      <div className="min-h-screen flex items-center justify-center">
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
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-6">
          <Alert>
            <AlertTitle>데이터 없음</AlertTitle>
            <AlertDescription className="mt-2">
              연습할 데이터가 없습니다.
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
      key={`${sessionIdParam}-${sessionTypeParam}`}
      currentItem={currentItem}
      sessionData={sessionData}
      onNext={handleNextWord}
      onPrevious={handlePreviousWord}
      recordingState={recordingState}
    >
        {isCompletingSession ? (
          // 세션 완료 처리 중일 때는 스피너 표시
          <div className="w-full h-full flex flex-col items-center justify-center gap-4 py-20">
            <Loader2 className="w-16 h-16 text-blue-500 animate-spin" strokeWidth={2} />
            <p className="text-xl font-semibold text-gray-700">세션 완료 처리 중...</p>
          </div>
        ) : (
          <PracticeComponent
            recordingState={recordingState}
            elapsed={elapsed}
            blobUrl={blobUrl}
            permissionError={permissionError}
            onStartRecording={startRecording}
            onStopRecording={stopRecording}
            onRetake={handleRetake}
            onUpload={handleUpload}
            isUploading={uploadState.isUploading}
            uploadError={uploadState.error}
            isCameraReady={!!isCameraReady}
            videoRef={videoRef}
          />
        )}
    </TrainingLayout>
  );
};

export default PracticePage;