import React from 'react';
import { TrendingDown } from 'lucide-react';

interface PromptCardDecrescendoProps {
  main: string;
  subtitle: string;
}

const PromptCardDecrescendo: React.FC<PromptCardDecrescendoProps> = ({ main, subtitle }) => {
  return (
    <div className="p-8 sm:p-10 bg-gradient-to-br from-purple-50 to-purple-100 rounded-2xl border-3 border-purple-300 shadow-sm mb-8 text-center">
      <div className="flex justify-center mb-4">
        <div className="p-3 bg-purple-200 rounded-full">
          <TrendingDown className="w-8 h-8 text-purple-700" strokeWidth={2.5} />
        </div>
      </div>
      <div className="flex justify-center items-end gap-1 mb-4">
        {[...main].map((char, i) => (
          <span
            key={i}
            className="font-extrabold text-purple-900 transition-all"
            style={{
              fontSize: `${80 - i * 12}px`,
              lineHeight: 1,
            }}
          >
            {char}
          </span>
        ))}
        <span className="font-extrabold text-purple-900" style={{ fontSize: '32px', lineHeight: 1 }}>
          ——
        </span>
      </div>
      <p className="text-xl sm:text-2xl font-bold text-purple-800 mb-3">
        {subtitle}
      </p>
      <div className="inline-block px-4 py-2 bg-purple-200/50 rounded-lg">
        <p className="text-base sm:text-lg text-purple-700 font-semibold">
          큰 소리에서 시작해서 점점 작게 발성해주세요
        </p>
      </div>
    </div>
  );
};

export default PromptCardDecrescendo;

