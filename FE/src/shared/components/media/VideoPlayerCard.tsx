import React, { useEffect, useRef, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/shared/components/ui/card";
import { Button } from "@/shared/components/ui/button";
import { Dialog, DialogContent, DialogTrigger, DialogTitle, DialogDescription } from "@/shared/components/ui/dialog";
import { Play, Repeat, Expand, Pause, Loader2, AlertCircle } from "lucide-react";
import type { VideoPlayerCardProps } from "@/shared/types/media";

/**
 * 비디오 플레이어 카드 컴포넌트
 * 순수 프레젠테이션 컴포넌트 - props로만 데이터와 콜백을 받습니다.
 */
const VideoPlayerCard: React.FC<VideoPlayerCardProps> = ({
  title,
  icon,
  videoSrc,
  dialogContent,
  flipHorizontal = false,
  isLoading = false,
  errorMessage,
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

  // src 변경 시 썸네일(첫 프레임) 즉시 반영
  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.pause();
      setIsPlaying(false);
      videoRef.current.load();
    }
  }, [videoSrc]);

  return (
    <Card className="w-full lg:w-[560px] shadow-lg rounded-xl">
      <CardHeader>
        <CardTitle
          className="flex items-center gap-2.5 text-2xl md:text-3xl font-semibold text-slate-800"
        >
          {icon}
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="px-6 pb-4">
        <div className="w-full h-80 bg-gray-100 rounded-xl overflow-hidden relative">
          {errorMessage ? (
            <div className="w-full h-full flex flex-col items-center justify-center text-center p-6">
              <AlertCircle className="w-12 h-12 text-red-500 mb-4" strokeWidth={2} />
              <p className="text-red-600 text-lg font-medium">{errorMessage}</p>
            </div>
          ) : isLoading ? (
            <div className="w-full h-full flex flex-col items-center justify-center">
              <Loader2 className="w-12 h-12 text-blue-500 animate-spin mb-4" strokeWidth={2} />
              <p className="text-gray-600 text-lg">동영상을 불러오는 중...</p>
            </div>
          ) : (
            <video
              ref={videoRef}
              className="w-full h-full object-cover"
              style={flipHorizontal ? { transform: 'scaleX(-1)' } : undefined}
              src={videoSrc}
              poster={videoSrc ? undefined : "https://placehold.co/510x323/e2e8f0/64748b?text=Video+Stream"}
              preload="metadata"
              playsInline
              onPlay={() => setIsPlaying(true)}
              onPause={() => setIsPlaying(false)}
              onEnded={() => setIsPlaying(false)}
            >
              브라우저가 비디오를 지원하지 않습니다.
            </video>
          )}
        </div>
      </CardContent>
      {!isLoading && !errorMessage && (
        <CardFooter className="h-auto min-h-10 flex justify-center items-center gap-5 px-6 pb-6">
          <Button
            variant="ghost"
            size="icon"
            onClick={handlePlayPause}
            className="text-slate-600 w-7 h-7"
            disabled={!videoSrc}
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
            className="text-slate-600 w-7 h-7"
            disabled={!videoSrc}
          >
            <Repeat className="w-full h-full" strokeWidth={2.5} />
          </Button>
          <Dialog>
            <DialogTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="text-slate-600 w-7 h-7"
                disabled={!videoSrc}
              >
                <Expand className="w-full h-full" strokeWidth={2.5} />
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-4xl w-full [&>button]:hidden">
              <DialogTitle className="sr-only">{title}</DialogTitle>
              <DialogDescription className="sr-only">
                {title} 동영상을 확대해서 볼 수 있습니다.
              </DialogDescription>
              {dialogContent}
            </DialogContent>
          </Dialog>
        </CardFooter>
      )}
    </Card>
  );
};

export default VideoPlayerCard;
export type { VideoPlayerCardProps };

