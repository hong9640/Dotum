import React from "react";
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { MonitorPlay, Camera, Play, Settings2, Expand } from "lucide-react";

// --- VideoPlayerCard 컴포넌트 (신규) ---
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
}

const VideoPlayerCard: React.FC<VideoPlayerCardProps> = ({
  title,
  icon,
  videoSrc,
}) => {
  return (
    // shadcn/ui Card를 기반으로, 사용자가 요청한 w-[560px]를 반응형으로 적용합니다.
    <Card className="w-full lg:w-[560px] shadow-lg rounded-xl">
      {/* 사용자가 요청한 px-6 pt-7 pb-6의 p-6과 유사합니다. */}
      <CardHeader>
        {/* pb-5 적용 */}
        <CardTitle
          className="flex items-center gap-2.5 text-2xl md:text-3xl font-semibold font-['Pretendard'] text-slate-800 pb-5"
        >
          {icon}
          {title}
        </CardTitle>
      </CardHeader>
      {/* CardContent는 기본 p-6 pt-0 이므로, 패딩을 조절합니다. */}
      <CardContent className="px-6 pb-4">
        {/* 비디오 플레이스홀더 영역 (h-80) */}
        <div className="w-full h-80 bg-gray-100 rounded-xl overflow-hidden">
          <img
            className="w-full h-full object-cover"
            src={
              videoSrc ||
              'https://placehold.co/510x323/e2e8f0/64748b?text=Video+Stream'
            }
            alt={title}
          />
        </div>
      </CardContent>
      {/* 컨트롤러 영역 (h-10, gap-5) */}
      <CardFooter className="h-10 flex justify-center items-center gap-5 px-6 pb-6">
        <Button
          variant="ghost"
          size="icon"
          className="text-slate-600 w-7 h-7"
        >
          <Play className="w-full h-full" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="text-slate-600 w-7 h-7"
        >
          <Settings2 className="w-full h-full" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="text-slate-600 w-7 h-7"
        >
          <Expand className="w-full h-full" />
        </Button>
      </CardFooter>
    </Card>
  );
};

// --- ResultVideoDisplay 컴포넌트 ---
/**
 * 훈련 결과 비디오 표시 컴포넌트
 * 두 개의 비디오 플레이어 카드를 나란히 배치합니다.
 */
const ResultVideoDisplay: React.FC = () => {
  return (
    // 카드들을 감싸는 flex 컨테이너. gap-8 적용.
    // 모바일에선 세로(flex-col), 데스크탑에선 가로(lg:flex-row)로 배치.
    <div className="flex flex-col lg:flex-row flex-wrap justify-center items-start gap-8">
      <VideoPlayerCard
        title="정확한 발음 (wav2lip)"
        icon={<MonitorPlay className="w-7 h-7 text-blue-600" />}
      />
      <VideoPlayerCard
        title="현재 내 발음 (사용자 녹화 영상)"
        icon={<Camera className="w-7 h-7 text-green-500" />}
      />
    </div>
  );
};

export default ResultVideoDisplay;
