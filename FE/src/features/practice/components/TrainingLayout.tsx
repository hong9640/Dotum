import React, { useEffect, useRef } from "react";
import ProgressHeader from "@/shared/components/layout/ProgressHeader";
import WordDisplay from "@/shared/components/display/WordDisplay";
import { type SessionItemResponse } from "@/features/training-session/api/session-item-search";
import { type CreateTrainingSessionResponse } from "@/features/training-session/api";

interface TrainingLayoutProps {
  currentItem: SessionItemResponse | null;
  sessionData: CreateTrainingSessionResponse | null;
  onNext: () => void;
  onPrevious: () => void;
  children: React.ReactNode;
  recordingState?: "idle" | "recording" | "processing" | "error";
}

const TrainingLayout: React.FC<TrainingLayoutProps> = ({
  currentItem,
  sessionData,
  onNext,
  onPrevious,
  children,
  recordingState = 'idle'
}) => {
  const wordDisplayRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // 컴포넌트가 마운트되거나 currentItem이 변경될 때 WordDisplay로 스크롤
    if (wordDisplayRef.current) {
      wordDisplayRef.current.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'start' 
      });
    }
  }, [currentItem]);

  return (
    <div className="min-h-screen">
      <div className="min-h-[1105px] px-8 sm:px-12 md:px-24 lg:px-32 py-6 flex justify-center items-start">
        <div className="w-full max-w-[1152px] flex flex-col gap-8">
          {/* 진행률 헤더 */}
          <ProgressHeader 
            step={currentItem ? currentItem.item_index + 1 : 1} 
            totalSteps={sessionData?.total_items ?? 1} 
          />

          {/* 발음할 단어 표시 */}
          <div id="word-display" ref={wordDisplayRef}>
            <WordDisplay 
              targetWord={currentItem ? (currentItem.word || currentItem.sentence || '') : ''}
              onNext={onNext}
              onPrevious={onPrevious}
              showNext={currentItem ? currentItem.has_next : false}
              showPrevious={currentItem ? currentItem.item_index > 0 : false}
              type={sessionData?.type}
              recordingState={recordingState}
            />
          </div>

          {/* 하위 컴포넌트 (practice 또는 result) */}
          {children}
        </div>
      </div>
    </div>
  );
};

export default TrainingLayout;
