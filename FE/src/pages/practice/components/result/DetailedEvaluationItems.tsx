import React from "react";
import { Volume2, AudioWaveform, GaugeCircle, Leaf, ListChecks } from "lucide-react";
import DetailedEvaluationItemCard, { type DetailedEvaluationItem } from "./DetailedEvaluationItemCard";

const evaluationData: DetailedEvaluationItem[] = [
  { id: "clarity", title: "명확도", score: 50, icon: Volume2, colorVariant: "green" },
  { id: "intonation", title: "억양", score: 90, icon: AudioWaveform, colorVariant: "blue" },
  { id: "speed", title: "속도", score: 40, icon: GaugeCircle, colorVariant: "amber" },
  { id: "naturalness", title: "자연스러움", score: 34, icon: Leaf, colorVariant: "amber" },
];

const DetailedEvaluationItems: React.FC = () => {
  return (
    <section className="w-full self-stretch border-t-2 border-slate-100 py-8">
      {/* <div className="mx-auto w-full max-w-6xl rounded-2xl border border-gray-200 bg-white p-4 shadow-lg sm:p-6"> */}
        <div className="pb-6 flex items-center">
          <ListChecks
            className="w-7 h-7 mr-3 text-green-500"
            strokeWidth={2.5}
          />
          <span className="text-slate-800 text-2xl md:text-3xl font-semibold leading-9">
            세부 평가 항목
          </span>
        </div>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:gap-6">
          {evaluationData.map((item) => (
            <DetailedEvaluationItemCard key={item.id} item={item} />
          ))}
        {/* </div> */}
      </div>
    </section>
  );
};

export default DetailedEvaluationItems;


