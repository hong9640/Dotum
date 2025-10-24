import React from "react";
import { usePracticeStore } from "@/stores/practiceStore";
import ProgressHeader from "@/components/ProgressHeader";
import WordDisplay from "@/components/WordDisplay";
import ResultVideoDisplay from "@/pages/result/components/ResultVideoDisplay";

const PracticePage: React.FC = () => {
  // 상태 관리
  const { 
    currentStep, 
    totalSteps, 
    currentWord, 
    nextStep, 
  } = usePracticeStore();


  return (
    <div className="min-h-screen bg-gray-50">
      <div className="min-h-[1105px] px-8 sm:px-12 md:px-24 lg:px-32 py-6 flex justify-center items-start">
        <div className="w-full max-w-[1152px] flex flex-col gap-8">
          {/* 진행률 헤더 */}
          <ProgressHeader step={currentStep} totalSteps={totalSteps} />

          {/* 발음할 단어 표시 */}
          <WordDisplay targetWord={currentWord} />
          <ResultVideoDisplay />
        </div>
      </div>
    </div>
  );
};

export default PracticePage;