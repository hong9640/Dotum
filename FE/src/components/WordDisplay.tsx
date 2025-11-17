import React from "react";
import { Volume2, VolumeX } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTTS } from "@/hooks/useTTS";
import { stopAllTTS } from "@/utils/tts";
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
  const [isPlaying, setIsPlaying] = React.useState(false);
  const { isSupported } = useTTS({
    lang: 'ko-KR',
    rate: 0.85, // 조금 느리게 (명확한 발음을 위해)
    pitch: 1.0,
    volume: 1.0,
  });

  // 단어가 변경되면 TTS 중지 및 상태 리셋
  React.useEffect(() => {
    stopAllTTS();
    setIsPlaying(false);
  }, [targetWord]);

  const handleTTSClick = () => {
    if (isPlaying) {
      return; // 재생 중에는 클릭 무시
    }
    
    setIsPlaying(true);
    
    // 안내 멘트 결정
    const isSentence = type === 'sentence' || targetWord.includes(' ') || targetWord.length > 10;
    const introText = isSentence 
      ? "다음 문장을 정확하게 읽어주세요" 
      : "다음 단어를 정확하게 읽어주세요";
    
    // 안내 멘트 먼저 재생
    const utterance1 = new SpeechSynthesisUtterance(introText);
    utterance1.lang = 'ko-KR';
    utterance1.rate = 0.85;
    utterance1.pitch = 1.0;
    utterance1.volume = 1.0;
    
    // 안내 멘트가 끝나면 잠시 후 단어/문장 재생
    utterance1.onend = () => {
      setTimeout(() => {
        // 두 번째 발화 생성
        const utterance2 = new SpeechSynthesisUtterance(targetWord);
        utterance2.lang = 'ko-KR';
        utterance2.rate = 0.85;
        utterance2.pitch = 1.0;
        utterance2.volume = 1.0;
        
        // 모든 재생이 끝나면 상태 해제
        utterance2.onend = () => {
          setIsPlaying(false);
        };
        
        utterance2.onerror = () => {
          setIsPlaying(false);
        };
        
        window.speechSynthesis.speak(utterance2);
      }, 200); // 0.2초 대기
    };
    
    utterance1.onerror = () => {
      setIsPlaying(false);
    };
    
    window.speechSynthesis.speak(utterance1);
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
                disabled={!targetWord || isPlaying || recordingState === 'recording'}
                className={`
                  shrink-0
                  size-12 sm:size-14
                  rounded-full
                  transition-all duration-200
                  ${isPlaying 
                    ? 'bg-green-500 text-white cursor-not-allowed opacity-70' 
                    : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                  }
                  disabled:cursor-not-allowed disabled:opacity-50
                `}
              >
                {isPlaying ? (
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
