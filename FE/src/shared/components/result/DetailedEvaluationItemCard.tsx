import React from "react";
import { Loader2 } from "lucide-react";
import type { DetailedEvaluationItem, EvaluationStatus } from "@/shared/types/result";

const statusStyles = {
  "좋음": {
    gradient: "from-green-50 to-green-100",
    border: "border-green-200",
    text: "text-green-700",
    icon: "text-green-600",
  },
  "주의": {
    gradient: "from-yellow-50 to-yellow-100",
    border: "border-yellow-200",
    text: "text-yellow-700",
    icon: "text-yellow-600",
  },
  "개선 필요": {
    gradient: "from-red-50 to-red-100",
    border: "border-red-200",
    text: "text-red-700",
    icon: "text-red-600",
  },
};

type Props = {
  item: DetailedEvaluationItem;
};

/**
 * 상세 평가 항목 카드 컴포넌트
 * 순수 프레젠테이션 컴포넌트 - props로만 데이터를 받습니다.
 */
const DetailedEvaluationItemCard: React.FC<Props> = ({ item }) => {
  const { title, status, icon: Icon, content } = item;
  const styles = statusStyles[status];

  return (
    <div className={`w-full p-6 bg-gradient-to-r rounded-2xl border-2 ${styles.gradient} ${styles.border} flex flex-col justify-start items-start gap-3`}>
      <div className="self-stretch flex justify-between items-center">
        <div className="flex justify-start items-center gap-3">
          <div className="pr-1 sm:pr-1.5 flex justify-start items-start">
            <div className="w-6 sm:w-8 h-6 sm:h-8 flex justify-center items-center">
              <Icon className={`w-6 sm:w-8 h-6 sm:h-8 ${styles.icon}`} strokeWidth={2.5} />
            </div>
          </div>
          <div className="flex justify-start items-center">
            <div className="text-slate-700 text-xl sm:text-[28px] font-semibold leading-9">
              {title}
            </div>
          </div>
        </div>
        <div className="px-4 py-1 bg-white/50 rounded-full flex justify-start items-center">
          <div className={`${styles.text} text-lg md:text-[20px] font-semibold leading-9`}>
            {status}
          </div>
        </div>
      </div>
      {content ? (
        <div className="self-stretch text-slate-600 text-xl md:text-[22px] font-semibold leading-relaxed px-1.5">
          {content}
        </div>
      ) : (
        <div className="self-stretch flex items-center justify-center py-4">
          <Loader2 className="w-8 h-8 text-blue-500 animate-spin" strokeWidth={2} />
        </div>
      )}
    </div>
  );
};

export default DetailedEvaluationItemCard;
export type { DetailedEvaluationItem, EvaluationStatus };

