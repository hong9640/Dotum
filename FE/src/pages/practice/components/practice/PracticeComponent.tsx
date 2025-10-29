import React from "react";
import RecordingPreview from "./RecordingPreview";
import RecordingControls from "./RecordingControls";
import RecordingResult from "./RecordingResult";
import RecordingTips from "./RecordingTips";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import type { RefObject } from "react";

interface PracticeComponentProps {
  recordingState: 'idle' | 'recording' | 'processing' | 'error';
  elapsed: number;
  blobUrl: string | null;
  permissionError: string | null;
  onStartRecording: () => void;
  onStopRecording: () => void;
  onRetake: () => void;
  onViewResults: () => void;
  onUpload?: () => void;
  isUploading?: boolean;
  uploadError?: string | null;
  isCameraReady?: boolean;
  videoRef: RefObject<HTMLVideoElement | null>;
}

const PracticeComponent: React.FC<PracticeComponentProps> = ({
  recordingState,
  elapsed,
  blobUrl,
  permissionError,
  onStartRecording,
  onStopRecording,
  onRetake,
  onViewResults,
  onUpload,
  isUploading = false,
  uploadError,
  isCameraReady = true,
  videoRef,
}) => {
  // 녹화 완료 후 결과 화면 표시
  if (recordingState === "idle" && blobUrl) {
    return (
      <>
        {/* 녹화 결과 */}
        <RecordingResult
          recordedBlobUrl={blobUrl}
          onRetake={onRetake}
          onUpload={onUpload}
          isUploading={isUploading}
          uploadError={uploadError}
          isVisible={true}
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
      </>
    );
  }

  return (
    <>
      {/* 녹화 미리보기 */}
      <RecordingPreview
        recordingState={recordingState}
        elapsed={elapsed}
        isCameraReady={isCameraReady}
        videoRef={videoRef}
      />

      {/* 녹화 컨트롤 */}
      <RecordingControls
        recordingState={recordingState}
        blobUrl={blobUrl}
        onStartRecording={onStartRecording}
        onStopRecording={onStopRecording}
        onRetake={onRetake}
        onViewResults={onViewResults}
        onUpload={onUpload}
        isUploading={isUploading}
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
    </>
  );
};

export default PracticeComponent;
