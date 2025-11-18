import React from "react";
import { Volume2, VolumeX } from "lucide-react";
import { Button } from "@/shared/components/ui/button";
import { useTTS } from "@/shared/hooks/useTTS";
// import { ChevronLeft, ChevronRight } from "lucide-react";

interface WordDisplayProps {
  targetWord: string;
  onPrevious?: () => void;
  onNext?: () => void;
  showPrevious?: boolean;
  showNext?: boolean;
  type?: 'word' | 'sentence' | 'vocal';
  recordingState?: "idle" | "recording" | "processing" | "error";
}

const WordDisplay: React.FC<WordDisplayProps> = ({
  targetWord,
  onPrevious: _onPrevious,
  onNext: _onNext,
  showPrevious: _showPrevious = false,
  showNext: _showNext = false,
  type = 'word',
  recordingState = 'idle'
}) => {
  const { speakWithIntro, stop, isSpeaking, isSupported } = useTTS({
    lang: 'ko-KR',
    rate: 0.85,
    pitch: 1.0,
    volume: 1.0,
  });

  // 단어가 변경되면 TTS 중지
  React.useEffect(() => {
    stop();
  }, [targetWord, stop]);

  const handleTTSClick = () => {
    if (!isSpeaking) {
      speakWithIntro(targetWord, type);
    }
  };

  return (
    <div className="flex flex-col items-center gap-6">
      <div className="flex items-center justify-center gap-6">
        {/* 이전 버튼 */}
        {/* {showPrevious ? (
          // <Button
          //   variant="ghost"
          //   size="icon"
          //   className="size-14 p-3 bg-slate-100 rounded-full border border-slate-200 hover:bg-slate-200"
          //   onClick={onPrevious}
          // >
          //   <ChevronLeft className="size-6 text-slate-600" />
          // </Button>
          <Button
            variant="ghost"
            size="icon"
            className="size-14 p-3 bg-green-500 rounded-full border border-green-500 hover:bg-green-600"
            onClick={onPrevious}
          >
            <ChevronLeft className="size-6 text-white" />
          </Button>
        ) : (
          <div className="size-14 p-3 bg-slate-100 rounded-full border border-slate-200 grid place-items-center">
            <ChevronLeft className="size-6 text-slate-600" />
          </div>
        )} */}

        {/* 단어 표시 */}
        <div className="px-2 sm:px-8 h-auto w-full max-w-4xl">
          <div className="h-min-24 h-auto flex items-center justify-center gap-4 sm:gap-6 relative">
            <p className={`text-center text-slate-800 font-bold leading-normal ${targetWord.includes(' ') || targetWord.length > 10
                ? 'text-3xl sm:text-4xl md:text-5xl'
                : 'text-5xl sm:text-7xl md:text-8xl'
              }`}>
              {targetWord}
            </p>
            
            {/* TTS 아이콘 버튼 */}
            {isSupported && (
              <Button
                variant="ghost"
                size="icon"
                onClick={handleTTSClick}
                disabled={!targetWord || isSpeaking || recordingState === 'recording'}
                className={`
                  shrink-0
                  size-12 sm:size-14
                  rounded-full
                  transition-all duration-200
                  ${isSpeaking 
                    ? 'bg-green-500 text-white cursor-not-allowed opacity-70' 
                    : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                  }
                  disabled:cursor-not-allowed disabled:opacity-50
                `}
              >
                {isSpeaking ? (
                  <VolumeX className="h-5 w-5 sm:h-6 sm:w-6" />
                ) : (
                  <Volume2 className="h-5 w-5 sm:h-6 sm:w-6" />
                )}
              </Button>
            )}
          </div>
        </div>

        {/* 다음 버튼 */}
        {/* {showNext ? (
          <Button
            variant="ghost"
            size="icon"
            className="size-14 p-3 bg-green-500 rounded-full border border-green-500 hover:bg-green-600"
            onClick={onNext}
          >
            <ChevronRight className="size-6 text-white" />
          </Button>
        ) : (
          // <div className="size-14 p-3 bg-green-500 rounded-full border border-slate-500 grid place-items-center">
          <div className="size-14 p-3 bg-slate-100 rounded-full border border-slate-200 grid place-items-center">
            <ChevronRight className="size-6 text-white" />
            <ChevronRight className="size-6 text-slate-600" />
          </div>
        )} */}
      </div>
      {/* <div className="text-center text-slate-500 text-xl sm:text-2xl md:text-3xl font-semibold">
        {type?.toLowerCase() === 'sentence' ? '위 문장을 또박또박 발음해주세요' : '위 단어를 또박또박 발음해주세요'}
      </div> */}
    </div>
  );
};

export default WordDisplay;
