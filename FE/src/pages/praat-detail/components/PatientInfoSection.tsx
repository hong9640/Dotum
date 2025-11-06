import React from "react";
import PraatSectionCard from "./PraatSectionCard";

export type PatientInfo = {
  analyzedAt?: string; // "2024년 1월 15일 14:30"
  word?: string; // 훈련 단어
};

export type PatientInfoSectionProps = {
  info: PatientInfo;
};

/**
 * 환자 정보 섹션 컴포넌트
 */
const PatientInfoSection: React.FC<PatientInfoSectionProps> = ({ info }) => {
  return (
    <PraatSectionCard
      title="환자 정보"
      titleIconClass="w-4 h-4 bg-blue-600"
      className="w-full"
    >
      <div className="flex flex-wrap gap-4">
        <div className="w-96">
          <div className="text-gray-500 text-sm">분석 일시</div>
          <div className="text-gray-900 text-base font-medium">
            {info.analyzedAt ?? "-"}
          </div>
        </div>
        <div className="w-96">
          <div className="text-gray-500 text-sm">훈련 단어</div>
          <div className="text-gray-900 text-base font-medium">
            {info.word ?? "-"}
          </div>
        </div>
      </div>
    </PraatSectionCard>
  );
};

export default PatientInfoSection;

