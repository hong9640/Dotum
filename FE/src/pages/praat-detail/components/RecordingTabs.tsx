import React from "react";
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
      titleIconClass="w-4 h-4 bg-blue-600"
      className="w-full"
    >
      <div className="pb-6 inline-flex justify-start items-start">
        <div className="w-full max-w-[1102px] h-12 p-1 bg-gray-100 rounded-xl flex justify-start items-start overflow-x-auto">
          {Array.from({ length: totalRecordings }, (_, index) => {
            const recordingNumber = index + 1;
            const isActive = index === currentRecordingIndex;
            
            return (
              <div
                key={index}
                className={`flex-shrink-0 ${index > 0 ? "pl-1" : ""} flex justify-start items-start`}
              >
                <button
                  onClick={() => onRecordingSelect(index)}
                  className={`w-96 h-10 px-4 py-2 rounded-md flex justify-center items-center transition-colors ${
                    isActive
                      ? "bg-white shadow-[0px_1px_2px_0px_rgba(0,0,0,0.04)]"
                      : ""
                  }`}
                >
                  <div className="pr-2 flex justify-start items-start">
                    <div className="w-3.5 h-3.5 relative overflow-hidden">
                      <div
                        className={`w-2.5 h-3 left-[1.51px] top-[0.88px] absolute ${
                          isActive ? "bg-blue-600" : "bg-gray-500"
                        }`}
                      />
                    </div>
                  </div>
                  <div
                    className={`text-center justify-center text-sm font-medium font-['Roboto'] leading-6 ${
                      isActive
                        ? "text-blue-600 [text-shadow:_0px_1px_2px_rgb(0_0_0_/_0.04)]"
                        : "text-gray-500"
                    }`}
                  >
                    {recordingNumber}번째 녹음
                  </div>
                </button>
              </div>
            );
          })}
        </div>
      </div>
    </PraatSectionCard>
  );
};

export default RecordingTabs;

