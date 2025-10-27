import React, { useState, useRef } from "react";
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogTrigger } from "@/components/ui/dialog";
import { Play, Repeat, Expand, Pause } from "lucide-react";

// --- VideoPlayerCard 컴포넌트 ---
/**
 * 비디오 플레이어 카드 컴포넌트
 * @param title 카드 제목
 * @param icon 카드 제목 옆에 표시될 아이콘 (ReactNode)
 * @param videoSrc 비디오/이미지 플레이스홀더 URL
 */
interface VideoPlayerCardProps {
  title: string;
  icon: React.ReactNode;
  videoSrc?: string;
  dialogContent: React.ReactNode;
}

const VideoPlayerCard: React.FC<VideoPlayerCardProps> = ({
  title,
  icon,
  videoSrc,
  dialogContent,
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

  return (
    // shadcn/ui Card를 기반으로, 사용자가 요청한 w-[560px]를 반응형으로 적용합니다.
    <Card className="w-full lg:w-[560px] shadow-lg rounded-xl">
      {/* 사용자가 요청한 px-6 pt-7 pb-6의 p-6과 유사합니다. */}
      <CardHeader>
        {/* pb-5 적용 */}
        <CardTitle
          className="flex items-center gap-2.5 text-2xl md:text-3xl font-semibold text-slate-800"
        >
          {icon}
          {title}
        </CardTitle>
      </CardHeader>
      {/* CardContent는 기본 p-6 pt-0 이므로, 패딩을 조절합니다. */}
      <CardContent className="px-6 pb-4">
        {/* 비디오 플레이어 영역 (h-80) */}
        <div className="w-full h-80 bg-gray-100 rounded-xl overflow-hidden relative">
          <video
            ref={videoRef}
            className="w-full h-full object-cover"
            src={videoSrc}
            poster="https://placehold.co/510x323/e2e8f0/64748b?text=Video+Stream"
            onPlay={() => setIsPlaying(true)}
            onPause={() => setIsPlaying(false)}
            onEnded={() => setIsPlaying(false)}
          >
            <source src={videoSrc} type="video/mp4" />
            브라우저가 비디오를 지원하지 않습니다.
          </video>
        </div>
      </CardContent>
      {/* 컨트롤러 영역 (h-10, gap-5) */}
      <CardFooter className="h-auto min-h-10 flex justify-center items-center gap-5 px-6 pb-6">
        <Button
          variant="ghost"
          size="icon"
          onClick={handlePlayPause}
          className="text-slate-600 w-7 h-7"
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
          className="text-slate-600 w-7 h-7"
        >
          <Repeat className="w-full h-full" strokeWidth={2.5} />
        </Button>
        <Dialog>
          <DialogTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="text-slate-600 w-7 h-7"
            >
              <Expand className="w-full h-full" strokeWidth={2.5} />
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-4xl w-full [&>button]:hidden">
            {dialogContent}
          </DialogContent>
        </Dialog>
      </CardFooter>
    </Card>
  );
};

export default VideoPlayerCard;
