import React from "react";
import PraatSectionCard from "./PraatSectionCard";

export type PatientInfo = {
  analyzedAt?: string; // "2024년 1월 15일"
  word?: string; // 훈련 단어 또는 훈련 명칭
  isVocalExercise?: boolean; // 발성 연습 여부
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
      title="녹음 파일 정보"
      titleIconClass="w-4 h-4 bg-blue-600"
      className="w-full"
    >
      <div className="flex flex-wrap gap-4 flex-col sm:flex-row">
        <div className="w-full flex-1">
          <div className="text-gray-500 text-sm sm:text-lg">분석 일시</div>
          <div className="text-gray-900 text-base sm:text-lg font-medium">
            {info.analyzedAt ?? "-"}
          </div>
        </div>
        <div className="w-full flex-1">
          <div className="text-gray-500 text-sm sm:text-lg">
            {info.isVocalExercise ? "훈련 명칭" : "훈련 단어"}
          </div>
          <div className="text-gray-900 text-base sm:text-lg font-medium">
            {info.word ?? "-"}
          </div>
        </div>
      </div>
    </PraatSectionCard>
  );
};

export default PatientInfoSection;

