import React from "react";
import { Mic } from "lucide-react";
import PraatSectionCard from "./PraatSectionCard";

export type RecordingTabsProps = {
  totalRecordings: number;
  currentRecordingIndex: number;
  onRecordingSelect: (index: number) => void;
};

/**
 * 녹음 횟수 탭 컴포넌트 (발성연습용)
 */
const RecordingTabs: React.FC<RecordingTabsProps> = ({
  totalRecordings,
  currentRecordingIndex,
  onRecordingSelect,
}) => {
  return (
    <PraatSectionCard
      title="녹음 결과 분석"
      titleIconClass="w-4 h-4 bg-teal-500"
      className="w-full"
    >
      <div className="pb-6 inline-flex justify-start items-start">
        <div className="w-full max-w-[1102px] flex justify-start items-start gap-3">
          {Array.from({ length: totalRecordings }, (_, index) => {
            const recordingNumber = index + 1;
            const isActive = index === currentRecordingIndex;
            
            return (
              <button
                key={index}
                onClick={() => onRecordingSelect(index)}
                className={`flex-1 min-w-0 h-14 px-6 py-3 rounded-xl flex justify-center items-center gap-2 transition-all ${
                  isActive
                    ? "bg-white shadow-[0px_2px_4px_0px_rgba(0,0,0,0.08)] border-2 border-blue-500"
                    : "bg-gray-100 hover:bg-gray-200 border-2 border-transparent"
                }`}
              >
                <Mic
                  className={`w-5 h-5 flex-shrink-0 ${
                    isActive ? "text-blue-600" : "text-gray-500"
                  }`}
                  strokeWidth={2.5}
                />
                <div
                  className={`text-center justify-center text-base font-semibold leading-6 whitespace-nowrap ${
                    isActive
                      ? "text-blue-600"
                      : "text-gray-600"
                  }`}
                >
                  {recordingNumber}번째 녹음
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </PraatSectionCard>
  );
};

export default RecordingTabs;

