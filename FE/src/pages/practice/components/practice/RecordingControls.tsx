import React, { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Square, RotateCcw, Upload } from "lucide-react";
// import { useNavigate } from "react-router-dom";

interface RecordingControlsProps {
  recordingState: "idle" | "recording" | "processing" | "error";
  blobUrl: string | null;
  onStartRecording: () => void;
  onStopRecording: () => void;
  onRetake: () => void;
  onViewResults?: () => void;
  onUpload?: () => void;
  isUploading?: boolean;
}

const RecordingControls: React.FC<RecordingControlsProps> = ({
  recordingState,
  blobUrl,
  onStartRecording,
  onStopRecording,
  onRetake,
  // onViewResults,
  onUpload,
  isUploading = false,
}) => {
  // const navigate = useNavigate();
  const [isProcessing, setIsProcessing] = useState(false);
  const timeoutRef = useRef<number | null>(null);
  const prevRecordingStateRef = useRef(recordingState);
  
  // recordingState나 isUploading이 실제로 변경되면 isProcessing 해제
  React.useEffect(() => {
    if (prevRecordingStateRef.current !== recordingState) {
      setIsProcessing(false);
      if (timeoutRef.current) {
        window.clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
    }
    prevRecordingStateRef.current = recordingState;
  }, [recordingState]);
  
  // isUploading이 true가 되면 isProcessing 해제
  React.useEffect(() => {
    if (isUploading) {
      setIsProcessing(false);
      if (timeoutRef.current) {
        window.clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
    }
  }, [isUploading]);

  // const handleViewResults = () => {
  //   if (onViewResults) {
  //     onViewResults();
  //   }
  //   navigate('/result');
  // };
  
  const handleStartRecording = () => {
    if (isProcessing || recordingState !== "idle") return;
    
    setIsProcessing(true);
    onStartRecording();
  };
  
  const handleStopRecording = () => {
    if (isProcessing || recordingState !== "recording") return;
    
    setIsProcessing(true);
    onStopRecording();
  };
  
  const handleUploadClick = () => {
    if (isProcessing || isUploading || !onUpload) return;
    
    setIsProcessing(true);
    onUpload();
  };
  
  return (
    <div className="flex justify-center gap-3 sm:gap-4">
      {recordingState === "idle" && !blobUrl && (
        <Button 
          size="lg" 
          className="px-8 py-6 text-xl bg-red-500 hover:bg-red-600 flex items-center gap-3" 
          onClick={handleStartRecording}
          disabled={isProcessing || recordingState !== "idle"}
        >
          <div className="relative">
            <div className="size-6 border-2 border-white rounded-full"></div>
            <div className="size-3 bg-white rounded-full absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2"></div>
          </div>
          녹화 시작
        </Button>
      )}

      {recordingState === "recording" && (
        <Button 
          size="lg" 
          className="px-8 py-6 text-xl bg-slate-800 hover:bg-slate-900 flex items-center gap-3" 
          onClick={handleStopRecording}
          disabled={isProcessing || recordingState !== "recording"}
        >
          <Square className="size-6 text-white" strokeWidth={2} />
          녹화 종료
        </Button>
      )}

      {recordingState === "idle" && blobUrl && (
        <div className="flex flex-wrap items-center justify-center gap-3">
          <Button 
            size="lg" 
            variant="secondary" 
            className="px-8 py-6 text-xl flex items-center gap-3" 
            onClick={onRetake}
            disabled={isUploading}
          >
            <RotateCcw className="size-6 text-slate-700" />
            다시 녹화
          </Button>
          {onUpload && (
            <Button 
              size="lg" 
              variant="default" 
              className="px-8 py-6 text-xl flex items-center gap-3" 
              onClick={handleUploadClick}
              disabled={isUploading || isProcessing}
            >
              <Upload className="size-6 text-white" />
              {isUploading ? "업로드 중..." : "영상 업로드"}
            </Button>
          )}
          {/* {onViewResults && (
            <Button 
              size="lg" 
              variant="outline" 
              className="px-8 py-6 text-xl flex items-center gap-3" 
              // onClick={handleViewResults}
            >
              결과 보기
            </Button>
          )} */}
        </div>
      )}
    </div>
  );
};

export default RecordingControls;
