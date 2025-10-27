import React from "react";
import { useNavigate } from "react-router-dom";
import { usePracticeStore } from "@/stores/practiceStore";
import ProgressHeader from "@/components/ProgressHeader";
import WordDisplay from "@/components/WordDisplay";
import ResultVideoDisplay from "@/pages/result/components/ResultVideoDisplay";
import FeedbackCard from "@/pages/result/components/FeedbackCard";

const ResultPage: React.FC = () => {
  const navigate = useNavigate();
  
  // 상태 관리
  const { 
    currentStep, 
    totalSteps, 
    currentWord,
    currentWordIndex,
    goToNextWord,
    goToPreviousWord
  } = usePracticeStore();

  const handleNextWord = () => {
    // 다음 단어로 이동
    goToNextWord();
    navigate('/practice');
  };

  const handlePreviousWord = () => {
    // 이전 단어로 이동
    goToPreviousWord();
    navigate('/practice');
  };

  const handleViewAllResults = () => {
    // 전체 결과 페이지로 이동
    navigate('/result-list');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="min-h-[1105px] px-8 sm:px-12 md:px-24 lg:px-32 py-6 flex justify-center items-start">
        <div className="w-full max-w-[1152px] flex flex-col gap-8">
          {/* 진행률 헤더 */}
          <ProgressHeader step={currentStep} totalSteps={totalSteps} />

          {/* 발음할 단어 표시 */}
          <WordDisplay 
            targetWord={currentWord}
            onNext={handleNextWord}
            onPrevious={handlePreviousWord}
            showNext={currentWordIndex < totalSteps - 1}
            showPrevious={currentWordIndex > 0}
          />
          <ResultVideoDisplay />
          <FeedbackCard onViewAllResults={handleViewAllResults} />
        </div>
      </div>
    </div>
  );
};

export default ResultPage;