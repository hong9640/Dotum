import React from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";

interface WordDisplayProps {
  targetWord: string;
  onPrevious?: () => void;
  onNext?: () => void;
  showPrevious?: boolean;
  showNext?: boolean;
}

const WordDisplay: React.FC<WordDisplayProps> = ({
  targetWord,
  onPrevious,
  onNext,
  showPrevious = false,
  showNext = false
}) => {
  return (
    <div className="flex flex-col items-center gap-6">
      <div className="flex items-center justify-center gap-6">
        {/* 이전 버튼 */}
        {showPrevious ? (
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
        )}

        {/* 단어 표시 */}
        <div className="px-2 sm:px-8 h-auto">
          <div className="h-min-24 h-auto grid place-items-center">
            <p className={`text-center text-slate-800 font-bold leading-normal ${targetWord.includes(' ') || targetWord.length > 10
                ? 'text-3xl sm:text-4xl md:text-5xl'
                : 'text-5xl sm:text-7xl md:text-8xl'
              }`}>
              {targetWord}
            </p>
          </div>
        </div>

        {/* 다음 버튼 */}
        {showNext ? (
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
            {/* <ChevronRight className="size-6 text-white" /> */}
            <ChevronRight className="size-6 text-slate-600" />
          </div>
        )}
      </div>
      <div className="text-center text-slate-500 text-xl sm:text-2xl md:text-3xl font-semibold">
        위 단어를 또박또박 발음해주세요
      </div>
    </div>
  );
};

export default WordDisplay;
