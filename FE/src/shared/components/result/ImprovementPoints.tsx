import React from "react";
import { Lightbulb, CheckCircle2 } from "lucide-react";

// 개선 포인트 항목 데이터 타입
type ImprovementPoint = string;

// 목업 데이터 (실서비스에서는 props 또는 API 연동 예정)
const improvementData: ImprovementPoint[] = [
  "단어 사이의 발음을 유지하고 속도를 일정하게 해보세요.",
  "문장 끝에서는 음 높이를 자연스럽게 내려보세요.",
];

/**
 * 개선 포인트 리스트 컴포넌트
 * 순수 프레젠테이션 컴포넌트 - 현재는 목업 데이터 사용
 */
const ImprovementPoints: React.FC = () => {
  return (
    <section className="w-full self-stretch pb-4">
      <div className="mx-auto w-full max-w-6xl rounded-2xl border-2 border-green-200 bg-green-50/50 py-6 px-4 shadow-lg sm:py-7 sm:px-5">
        {/* 타이틀 영역 */}
        <div className="pb-5 flex items-center">
          <Lightbulb
            className="w-7 h-7 mr-2 text-green-500"
            strokeWidth={2.5}
          />
          <span className="text-slate-800 text-2xl md:text-3xl font-semibold">
            개선 포인트
          </span>
        </div>
        {/* 개선 포인트 항목 리스트 */}
        <div className="flex w-full flex-col gap-3">
          {improvementData.map((point, index) => (
            <div
              key={index}
              className="flex w-full items-center gap-3 rounded-xl bg-white p-4 shadow-sm ring-1 ring-gray-900/5"
            >
              <div className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full text-green-600">
                <CheckCircle2 className="h-5 w-5" />
              </div>
              <p className="flex-1 text-base font-medium text-slate-700 sm:text-lg">{point}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default ImprovementPoints;

