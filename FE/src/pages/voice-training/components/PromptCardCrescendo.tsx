import React from 'react';

interface PromptCardCrescendoProps {
  main: string;
  subtitle: string;
  attempt: number;
  totalAttempts: number;
}

const PromptCardCrescendo: React.FC<PromptCardCrescendoProps> = ({ main, subtitle, attempt, totalAttempts }) => {
  return (
    <div className="p-8 sm:p-10 bg-gradient-to-br from-teal-50 to-teal-100 rounded-2xl border-3 border-teal-300 shadow-sm mb-8 text-center">
      <div className="text-2xl sm:text-3xl font-bold text-teal-800 mb-4">
        {attempt}/{totalAttempts}
      </div>
      <div className="flex justify-center items-end gap-1 mb-4">
        {[...main].map((char, i) => (
          <span
            key={i}
            className="font-extrabold text-teal-900 transition-all"
            style={{
              fontSize: `${32 + i * 12}px`,
              lineHeight: 1,
            }}
          >
            {char}
          </span>
        ))}
        <span className="font-extrabold text-teal-900" style={{ fontSize: '80px', lineHeight: 1 }}>
          ——
        </span>
      </div>
      <p className="text-xl sm:text-2xl font-bold text-teal-800 mb-3">
        {subtitle}
      </p>
      <div className="inline-block px-4 py-2 bg-teal-200/50 rounded-lg">
        <p className="text-base sm:text-lg text-teal-700 font-semibold">
          작은 소리에서 시작해서 점점 크게 발성해주세요
        </p>
      </div>
    </div>
  );
};

export default PromptCardCrescendo;

