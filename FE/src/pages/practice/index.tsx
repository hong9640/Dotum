import React from "react";
import { useNavigate } from "react-router-dom";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useMediaRecorder } from "@/hooks/useMediaRecorder";
import { usePracticeStore } from "@/stores/practiceStore";
import ProgressHeader from "@/components/ProgressHeader";
import WordDisplay from "@/components/WordDisplay";
import RecordingPreview from "@/pages/practice/components/RecordingPreview";
import RecordingControls from "@/pages/practice/components/RecordingControls";
import RecordingTips from "@/pages/practice/components/RecordingTips";

const PracticePage: React.FC = () => {
  const navigate = useNavigate();
  
  // 상태 관리
  const { 
    currentStep, 
    totalSteps, 
    currentWord, 
    currentWordIndex,
    addRecordedVideo,
    goToNextWord,
    goToPreviousWord
  } = usePracticeStore();

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