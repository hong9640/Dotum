import React from 'react';
import { Volume2 } from 'lucide-react';

interface PromptCardMPTProps {
  main: string;
  subtitle: string;
  onPlayGuide?: () => void;
}

const PromptCardMPT: React.FC<PromptCardMPTProps> = ({ main, subtitle, onPlayGuide }) => {
  return (
    <div className="p-8 sm:p-10 bg-gradient-to-br from-blue-50 to-blue-100 rounded-2xl border-3 border-blue-300 shadow-sm mb-8 text-center">
      <div className="flex justify-center mb-4">
        <button
          onClick={onPlayGuide}
          className="p-3 bg-blue-200 rounded-full hover:bg-blue-300 transition-colors cursor-pointer"
          aria-label="안내 듣기"
        >
          <Volume2 className="w-8 h-8 text-blue-700" strokeWidth={2.5} />
        </button>
      </div>
      <h1 className="text-6xl sm:text-7xl font-extrabold text-blue-900 mb-4">
        {main}——
      </h1>
      <p className="text-xl sm:text-2xl font-bold text-blue-800 mb-3">
        {subtitle}
      </p>
      <div className="inline-block px-4 py-2 bg-blue-200/50 rounded-lg">
        <p className="text-base sm:text-lg text-blue-700 font-semibold">
          편안하게 최대한 길게 발성해주세요
        </p>
      </div>
    </div>
  );
};

export default PromptCardMPT;

