import React, { useEffect, useRef, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { DialogClose } from "@/components/ui/dialog";
import { Play, Pause, Repeat, Minimize2 } from "lucide-react";

// --- LargeVideoPlayer 컴포넌트 ---
/**
 * Dialog 내부에 표시될 큰 비디오 플레이어 컴포넌트
 */
interface LargeVideoPlayerProps {
  title: string;
  icon: React.ReactNode;
  videoSrc?: string;
  posterSrc?: string;
  flipHorizontal?: boolean; // 좌우 반전 여부
}

const LargeVideoPlayer: React.FC<LargeVideoPlayerProps> = ({
  title,
  icon,
  videoSrc,
  posterSrc,
  flipHorizontal = false,
}) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);

  const handlePlayPause = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const handleReplay = () => {
    if (!videoRef.current) return;
    videoRef.current.pause();
    videoRef.current.currentTime = 0;
    videoRef.current.play();
  };

  // videoSrc 변경 시 비디오를 새로 로드하여 반영
  useEffect(() => {
    if (videoRef.current) {
      // 일시정지 후 새 소스 로드
      videoRef.current.pause();
      setIsPlaying(false);
      // 강제 리로드
      videoRef.current.load();
    }
  }, [videoSrc]);

  return (
    <Card className="w-full border-0 shadow-none p-0">
      <CardHeader className="p-0 pb-5 flex flex-row justify-between items-center">
        <CardTitle className="flex items-center text-slate-800 text-2xl md:text-3xl font-semibold leading-9">
          {icon}
          {title}
        </CardTitle>
        <DialogClose asChild>
          <Button variant="ghost" size="icon" className="text-slate-600 !mt-0">
            <Minimize2 className="w-7 h-7" strokeWidth={2.5}/>
          </Button>
        </DialogClose>
      </CardHeader>
      <CardContent className="p-0 pb-4">
        {/* 비디오만 반전하기 위해 video 엘리먼트에만 직접 적용 */}
        <div className="w-full h-[300px] sm:h-[400px] md:h-[455px] bg-gray-100 rounded-xl overflow-hidden relative">
          <video
            ref={videoRef}
            className="w-full h-full object-cover"
            style={flipHorizontal ? { transform: 'scaleX(-1)' } : undefined}
            src={videoSrc}
            poster={videoSrc ? undefined : (posterSrc || "https://placehold.co/867x549/e2e8f0/64748b?text=Large+Video")}
            preload="metadata"
            playsInline
            onPlay={() => setIsPlaying(true)}
            onPause={() => setIsPlaying(false)}
            onEnded={() => setIsPlaying(false)}
          >
            브라우저가 비디오를 지원하지 않습니다.
          </video>
        </div>
      </CardContent>
      <CardFooter className="p-0 h-10 flex justify-center items-center gap-5">
        <Button
          variant="ghost"
          size="icon"
          onClick={handlePlayPause}
          className="text-slate-600 w-8 h-8"
        >
          {isPlaying ? (
            <Pause className="w-full h-full" strokeWidth={2.5} />
          ) : (
            <Play className="w-full h-full" strokeWidth={2.5} />
          )}
        </Button>
        <Button
          variant="ghost"
          size="icon"
          onClick={handleReplay}
          className="text-slate-600 w-8 h-8"
        >
          <Repeat className="w-full h-full" strokeWidth={2.5} />
        </Button>
      </CardFooter>
    </Card>
  );
};

export default LargeVideoPlayer;



