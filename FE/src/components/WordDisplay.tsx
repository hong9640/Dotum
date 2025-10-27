import React from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

interface WordDisplayProps {
  targetWord: string;
}

const WordDisplay: React.FC<WordDisplayProps> = ({ targetWord }) => {
  return (
    <div className="flex flex-col items-center gap-6">
      <div className="flex items-center justify-center gap-6">
        <div className="size-14 p-3 bg-slate-100 rounded-full border border-slate-200 grid place-items-center">
          <ChevronLeft className="size-6 text-slate-600" />
        </div>
        <div className="px-2 sm:px-8">
          <div className="h-24 grid place-items-center">
            <p className="text-center text-slate-800 text-5xl sm:text-7xl md:text-8xl font-bold font-[Inter] leading-none">
              {targetWord}
            </p>
          </div>
        </div>
        <div className="size-14 p-3 bg-green-500 rounded-full border border-green-500 grid place-items-center">
          <ChevronRight className="size-6 text-white" />
        </div>
      </div>
      <div className="text-center text-slate-500 text-xl sm:text-2xl md:text-3xl font-semibold">
        위 단어를 또박또박 발음해주세요
      </div>
    </div>
  );
};

export default WordDisplay;
