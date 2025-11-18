import React from "react";
import RecordingPreview from "./RecordingPreview";
import RecordingControls from "./RecordingControls";
import RecordingResult from "./RecordingResult";
import RecordingTips from "./RecordingTips";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/shared/components/ui/alert-dialog";
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

        {/* 권한 에러 다이얼로그 */}
        <AlertDialog open={!!permissionError}>
          <AlertDialogContent className="max-w-lg">
            <AlertDialogHeader className="text-center space-y-4">
              <AlertDialogTitle className="text-[30px]">카메라/마이크 접근 실패</AlertDialogTitle>
              <div className="text-[20px] text-muted-foreground space-y-3">
                <p>브라우저에서 권한이 차단된 상태입니다.</p>
                <div className="text-left bg-slate-100 p-4 rounded-lg space-y-2 text-[18px]">
                  <p className="font-semibold">권한 허용 방법:</p>
                  <ol className="list-decimal list-inside space-y-1">
                    <li>주소창 왼쪽의 ℹ️ 아이콘 클릭</li>
                    <li>"카메라" 및 "마이크" 권한 변경</li>
                    <li>페이지 새로고침</li>
                  </ol>
                </div>
              </div>
            </AlertDialogHeader>
            <AlertDialogFooter className="flex-col gap-3 sm:flex-col">
              <AlertDialogAction 
                onClick={() => window.location.reload()}
                className="w-full text-[30px] h-16"
              >
                페이지 새로고침
              </AlertDialogAction>
              <AlertDialogCancel 
                onClick={() => window.history.back()}
                className="w-full text-[30px] h-16 m-0"
              >
                취소
              </AlertDialogCancel>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
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

      {/* 권한 에러 다이얼로그 */}
      <AlertDialog open={!!permissionError}>
        <AlertDialogContent className="max-w-lg">
          <AlertDialogHeader className="text-center space-y-4">
            <AlertDialogTitle className="text-[30px]">카메라/마이크 접근 실패</AlertDialogTitle>
            <div className="text-[20px] text-muted-foreground space-y-3">
              <p>브라우저에서 권한이 차단된 상태입니다.</p>
              <div className="text-left bg-slate-100 p-4 rounded-lg space-y-2 text-[18px]">
                <p className="font-semibold">권한 허용 방법:</p>
                <ol className="list-decimal list-inside space-y-1">
                  <li>주소창 왼쪽의 ℹ️ 아이콘 클릭</li>
                  <li>"카메라" 및 "마이크" 권한 변경</li>
                  <li>페이지 새로고침</li>
                </ol>
              </div>
            </div>
          </AlertDialogHeader>
          <AlertDialogFooter className="flex-col gap-3 sm:flex-col">
            <AlertDialogAction 
              onClick={() => window.location.reload()}
              className="w-full text-[30px] h-16"
            >
              페이지 새로고침
            </AlertDialogAction>
            <AlertDialogCancel 
              onClick={() => window.history.back()}
              className="w-full text-[30px] h-16 m-0"
            >
              취소
            </AlertDialogCancel>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};

export default PracticeComponent;
