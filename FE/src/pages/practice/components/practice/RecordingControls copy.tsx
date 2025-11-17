import React from "react";
import { Button } from "@/components/ui/button";
import { Square, RotateCcw, Upload } from "lucide-react";
import { useNavigate } from "react-router-dom";

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
  onViewResults,
  onUpload,
  isUploading = false,
}) => {
  const navigate = useNavigate();

  const handleViewResults = () => {
    if (onViewResults) {
      onViewResults();
    }
    navigate('/result');
  };
  return (
    <div className="flex justify-center gap-3 sm:gap-4">
      {recordingState === "idle" && !blobUrl && (
        <Button size="lg" className="px-8 py-6 text-xl bg-red-500 hover:bg-red-600 flex items-center gap-3" onClick={onStartRecording}>
          <div className="relative">
            <div className="size-6 border-2 border-white rounded-full"></div>
            <div className="size-3 bg-white rounded-full absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2"></div>
          </div>
          녹화 시작
        </Button>
      )}

      {recordingState === "recording" && (
        <Button size="lg" className="px-8 py-6 text-xl bg-slate-800 hover:bg-slate-900 flex items-center gap-3" onClick={onStopRecording}>
          <Square className="size-6 text-white" strokeWidth={2} />
          녹화 종료
        </Button>
      )}

      {recordingState === "idle" && blobUrl && (
        <div className="flex flex-wrap items-center justify-center gap-3">
          <Button size="lg" variant="secondary" className="px-8 py-6 text-xl flex items-center gap-3" onClick={onRetake}>
            <RotateCcw className="size-6 text-slate-700" />
            다시 녹화
          </Button>
          {onUpload && (
            <Button 
              size="lg" 
              variant="default" 
              className="px-8 py-6 text-xl flex items-center gap-3" 
              onClick={onUpload}
              disabled={isUploading}
            >
              <Upload className="size-6 text-white" />
              {isUploading ? "업로드 중..." : "영상 업로드"}
            </Button>
          )}
          {onViewResults && (
            <Button 
              size="lg" 
              variant="outline" 
              className="px-8 py-6 text-xl flex items-center gap-3" 
              onClick={handleViewResults}
            >
              결과 보기
            </Button>
          )}
        </div>
      )}
    </div>
  );
};

export default RecordingControls;
