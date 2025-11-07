import React from 'react';

interface PromptCardSoftLoudProps {
  main: string;
  subtitle: string;
}

const PromptCardSoftLoud: React.FC<PromptCardSoftLoudProps> = ({ main, subtitle }) => {
  const sizes = [32, 56, 80, 88, 80];
  
  return (
    <div className="p-8 sm:p-10 bg-gradient-to-br from-pink-50 to-pink-100 rounded-2xl border-3 border-pink-300 shadow-sm mb-8 text-center">
      <div className="flex justify-center items-end gap-1 mb-4">
        {[...main].map((char, i) => (
          <span
            key={i}
            className="font-extrabold text-pink-900 transition-all"
            style={{
              fontSize: `${sizes[i]}px`,
              lineHeight: 1,
            }}
          >
            {char}
          </span>
        ))}
        <span className="font-extrabold text-pink-900" style={{ fontSize: '80px', lineHeight: 1 }}>
          ——
        </span>
      </div>
      <p className="text-xl sm:text-2xl font-bold text-pink-800 mb-3">
        {subtitle}
      </p>
      <div className="inline-block px-4 py-2 bg-pink-200/50 rounded-lg">
        <p className="text-base sm:text-lg text-pink-700 font-semibold">
          작게 → 조금 크게 → 크게 → 더 크게 변화를 주며 발성해주세요
        </p>
      </div>
    </div>
  );
};

export default PromptCardSoftLoud;

