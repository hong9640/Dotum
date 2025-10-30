import React from "react";
import ProgressHeader from "@/components/ProgressHeader";
import WordDisplay from "@/components/WordDisplay";
import { type CurrentItemResponse } from "@/api/training-session/currentItem";
import { type CreateTrainingSessionResponse } from "@/api/training-session";

interface TrainingLayoutProps {
  currentItem: CurrentItemResponse | null;
  sessionData: CreateTrainingSessionResponse | null;
  onNext: () => void;
  onPrevious: () => void;
  children: React.ReactNode;
}

const TrainingLayout: React.FC<TrainingLayoutProps> = ({
  currentItem,
  sessionData,
  onNext,
  onPrevious,
  children
}) => {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="min-h-[1105px] px-8 sm:px-12 md:px-24 lg:px-32 py-6 flex justify-center items-start">
        <div className="w-full max-w-[1152px] flex flex-col gap-8">
          {/* 진행률 헤더 */}
          <ProgressHeader 
            step={currentItem ? currentItem.item_index + 1 : 1} 
            totalSteps={sessionData ? sessionData.total_items : 1} 
          />

          {/* 발음할 단어 표시 */}
          <WordDisplay 
            targetWord={currentItem ? (currentItem.word || currentItem.sentence || '') : ''}
            onNext={onNext}
            onPrevious={onPrevious}
            showNext={currentItem ? currentItem.has_next : false}
            showPrevious={currentItem ? currentItem.item_index > 0 : false}
          />

          {/* 하위 컴포넌트 (practice 또는 result) */}
          {children}
        </div>
      </div>
    </div>
  );
};

export default TrainingLayout;
