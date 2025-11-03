import React from "react";
import { MonitorPlay, User } from "lucide-react";
import VideoPlayerCard from "./VideoPlayerCard";
import LargeVideoPlayer from "./LargeVideoPlayer";
// URL 파라미터/사전서명 조회는 제거. 업로드 응답의 video_url을 직접 전달받아 사용


// --- ResultVideoDisplay 컴포넌트 ---
/**
 * 훈련 결과 비디오 표시 컴포넌트
 * 두 개의 비디오 플레이어 카드를 나란히 배치합니다.
 */
interface ResultVideoDisplayProps {
  userVideoUrl?: string;
  compositedVideoUrl?: string;
  isLoadingCompositedVideo?: boolean;
  compositedVideoError?: string | null;
}

const ResultVideoDisplay: React.FC<ResultVideoDisplayProps> = ({ 
  userVideoUrl,
  compositedVideoUrl,
  isLoadingCompositedVideo = false,
  compositedVideoError,
}) => {
  return (
    // 카드들을 감싸는 flex 컨테이너. gap-8 적용.
    // 모바일에선 세로(flex-col), 데스크탑에선 가로(lg:flex-row)로 배치.
    <div className="flex flex-col lg:flex-row flex-wrap justify-center items-start gap-8">
      <VideoPlayerCard
        title="정확한 발음 (wav2lip)"
        icon={<MonitorPlay className="w-7 h-7 text-blue-600" />}
        videoSrc={compositedVideoUrl}
        isLoading={isLoadingCompositedVideo}
        errorMessage={compositedVideoError || undefined}
        flipHorizontal={true}
        dialogContent={
          <LargeVideoPlayer
            title="정확한 발음 (wav2lip)"
            icon={<MonitorPlay className="w-8 h-8 mr-2.5 text-blue-600" strokeWidth={2} />}
            videoSrc={compositedVideoUrl}
            posterSrc="https://placehold.co/867x549/e2e8f0/64748b?text=Wav2Lip+Video"
            flipHorizontal={true}
          />
        }
      />
      <VideoPlayerCard
        title="현재 내 발음 (사용자 녹화 영상)"
        icon={<User className="w-7 h-7 text-green-500" />}
        videoSrc={userVideoUrl || ""}
        flipHorizontal={true}
        dialogContent={
          <LargeVideoPlayer
            key={userVideoUrl || 'empty-user-video'}
            title="현재 내 발음 (사용자 녹화 영상)"
            icon={<User className="w-8 h-8 mr-2.5 text-green-500" strokeWidth={2} />}
            videoSrc={userVideoUrl || ""}
            posterSrc="https://placehold.co/867x549/e2e8f0/64748b?text=User+Video"
            flipHorizontal={true}
          />
        }
      />
    </div>
  );
};

export default ResultVideoDisplay;
