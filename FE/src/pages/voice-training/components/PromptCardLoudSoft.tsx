import React from 'react';

interface PromptCardLoudSoftProps {
  main: string;
  subtitle: string;
}

const PromptCardLoudSoft: React.FC<PromptCardLoudSoftProps> = ({ main, subtitle }) => {
  const sizes = [80, 88, 80, 56, 32];
  
  return (
    <div className="p-8 sm:p-10 bg-gradient-to-br from-orange-50 to-orange-100 rounded-2xl border-3 border-orange-300 shadow-sm mb-8 text-center">
      <div className="flex justify-center items-end gap-1 mb-4">
        {[...main].map((char, i) => (
          <span
            key={i}
            className="font-extrabold text-orange-900 transition-all"
            style={{
              fontSize: `${sizes[i]}px`,
              lineHeight: 1,
            }}
          >
            {char}
          </span>
        ))}
        <span className="font-extrabold text-orange-900" style={{ fontSize: '32px', lineHeight: 1 }}>
          ——
        </span>
      </div>
      <p className="text-xl sm:text-2xl font-bold text-orange-800 mb-3">
        {subtitle}
      </p>
      <div className="inline-block px-4 py-2 bg-orange-200/50 rounded-lg">
        <p className="text-base sm:text-lg text-orange-700 font-semibold">
          크게 → 더 크게 → 작게 → 더 작게 변화를 주며 발성해주세요
        </p>
      </div>
    </div>
  );
};

export default PromptCardLoudSoft;

