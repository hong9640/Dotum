import React, { useState } from "react";
import ReactPlayer from "react-player";
import { Play, RotateCcw } from "lucide-react";

interface RecordingResultProps {
  recordedBlobUrl: string | null;
  onRetake: () => void;
  onUpload?: () => void;
  isUploading?: boolean;
  uploadError?: string | null;
  isVisible: boolean;
}

const RecordingResult: React.FC<RecordingResultProps> = ({
  recordedBlobUrl,
  onRetake,
  onUpload,
  isUploading = false,
  uploadError,
  isVisible,
}) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [playerKey, setPlayerKey] = useState(0);

  if (!isVisible || !recordedBlobUrl) return null;

  const handleReplay = () => {
    setIsPlaying(false);
    setPlayerKey(prev => prev + 1);
    setTimeout(() => {
      setIsPlaying(true);
    }, 100);
  };

  return (
    <div className="flex justify-center">
      <div className="w-full max-w-[800px]">
        {/* 완료 안내 메시지 */}
        <div className="text-center mb-4">
          <div className="px-6 py-3 bg-green-600/90 rounded-full inline-block">
            <span className="text-white text-base sm:text-lg md:text-xl font-semibold">
              녹화 완료! 영상을 확인해보세요
            </span>
          </div>
        </div>

        {/* 영상 */}
        <div className="w-full max-w-[800px] rounded-2xl overflow-hidden">
          <div className="relative aspect-video bg-slate-900">
            {/* 녹화된 비디오 재생 */}
            <div className="absolute inset-0 overflow-hidden">
              <ReactPlayer
                key={playerKey}
                src={recordedBlobUrl}
                controls={false}
                playing={isPlaying}
                loop={false}
                width="100%"
                height="100%"
                style={{ transform: 'scaleX(-1)' }}
                onEnded={() => setIsPlaying(false)}
              />
            </div>
          </div>
        </div>

        {/* 액션 버튼들 - 영상 밖 아래 */}
        <div className="text-center mt-6">
          {/* 업로드 에러 표시 */}
          {uploadError && (
            <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg">
              <p className="font-semibold">업로드 실패</p>
              <p>{uploadError}</p>
            </div>
          )}
          
          <div className="flex justify-center gap-4">
            <button
              onClick={() => setIsPlaying(!isPlaying)}
              className="flex items-center justify-center gap-2 px-8 py-4 bg-blue-500 hover:bg-blue-600 text-white rounded-full font-semibold transition-colors text-lg"
            >
              <Play className="size-5" />
              {isPlaying ? "일시정지" : "재생"}
            </button>
            <button
              onClick={handleReplay}
              className="flex items-center justify-center gap-2 px-8 py-4 bg-slate-500 hover:bg-gray-600 text-white rounded-full font-semibold transition-colors text-lg"
            >
              <RotateCcw className="size-5" />
              다시 재생
            </button>
            <button
              onClick={onRetake}
              className="px-8 py-4 bg-red-500 hover:bg-red-600 text-white rounded-full font-semibold transition-colors text-lg"
            >
              다시 녹화
            </button>
            {onUpload && (
              <button
                onClick={onUpload}
                disabled={isUploading}
                className="px-8 py-4 bg-green-500 hover:bg-green-600 disabled:bg-gray-400 disabled:cursor-not-allowed text-white rounded-full font-semibold transition-colors text-lg"
              >
                {isUploading ? "업로드 중..." : "영상 업로드"}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default RecordingResult;
