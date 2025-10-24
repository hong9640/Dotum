import React from "react";

// --- PronunciationScore 컴포넌트 ---
/**
 * 발음 유사도 점수 표시 컴포넌트
 */
interface PronunciationScoreProps {
  similarity?: number;
}

const PronunciationScore: React.FC<PronunciationScoreProps> = ({ 
  similarity = 87 
}) => {
  return (
    <div className="px-6 pt-7 pb-6 bg-green-50 rounded-2xl border-2 border-green-200">
      <div className="flex flex-col items-center pb-5">
        <div className="pb-3.5">
          <span className="text-center text-green-500 text-4xl md:text-5xl font-extrabold font-['Pretendard'] leading-[48px]">
            {similarity}%
          </span>
        </div>
        <div>
          <span className="text-center text-gray-700 text-2xl md:text-3xl font-semibold font-['Pretendard'] leading-9">
            발음 유사도
          </span>
        </div>
      </div>
      {/* 프로그레스 바 */}
      <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden">
        <div
          className="h-3 bg-green-400 rounded-full"
          style={{ width: `${similarity}%` }}
        />
      </div>
    </div>
  );
};

export default PronunciationScore;
