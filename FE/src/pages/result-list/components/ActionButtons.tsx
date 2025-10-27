import React from 'react';
import { RefreshCw, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ActionButtonsProps {
  onRetry: () => void;
  onNewTraining: () => void;
}

const ActionButtons: React.FC<ActionButtonsProps> = ({ onRetry, onNewTraining }) => {
  return (
    <div className="w-full max-w-[1220.40px] p-6 bg-white rounded-2xl outline outline-[3px] outline-offset-[-3px] outline-slate-200 flex flex-col justify-start items-center gap-9">
      <div className="self-stretch h-auto md:h-10 inline-flex justify-center items-center gap-3">
        <div className="w-7 flex justify-center items-center gap-2.5">
          <div className="justify-start text-neutral-950 text-2xl md:text-3xl font-semibold leading-tight md:leading-9">
            🌱
          </div>
        </div>
        <div className="flex justify-center items-center gap-2.5">
          <h2 className="justify-start text-gray-800 text-2xl md:text-3xl font-semibold leading-tight md:leading-9">
            다음은 무엇을 하고 싶으세요?
          </h2>
        </div>
      </div>
      <div className="h-auto inline-flex flex-col md:flex-row justify-start items-start gap-4 w-full">
        <Button
          variant="outline"
          className="w-full md:w-[571px] min-h-10 h-auto px-6 py-4 bg-white rounded-xl outline outline-2 outline-green-500 flex justify-center items-center gap-3 text-green-500 hover:bg-green-50 transition-colors"
          onClick={onRetry}
        >
          <RefreshCw className="w-6 h-6 md:w-8 md:h-8" strokeWidth={2.5} />
          <span className="text-center justify-center text-xl md:text-3xl font-semibold leading-snug md:leading-9">
            다시 연습하기
          </span>
        </Button>
        <Button
          className="w-full md:w-[571px] min-h-10 h-auto px-6 py-4 bg-gradient-to-r from-violet-500 via-indigo-400 to-cyan-400 rounded-xl flex justify-center items-center gap-3 text-white hover:opacity-90 transition-opacity"
          onClick={onNewTraining}
        >
          <Sparkles className="w-6 h-6 md:w-8 md:h-8" strokeWidth={2.5} />
          <span className="text-center justify-center text-xl md:text-3xl font-semibold leading-snug md:leading-9">
            새로운 훈련 시작
          </span>
        </Button>
      </div>
    </div>
  );
};

export default ActionButtons;
