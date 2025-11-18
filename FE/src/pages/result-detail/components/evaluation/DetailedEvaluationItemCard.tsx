import React from "react";

export type EvaluationStatus = "좋음" | "주의" | "개선 필요";

export type DetailedEvaluationItem = {
  id: string;
  title: string;
  status: EvaluationStatus;
  icon: React.ElementType;
};

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

const DetailedEvaluationItemCard: React.FC<Props> = ({ item }) => {
  const { title, status, icon: Icon } = item;
  const styles = statusStyles[status];

  return (
    <div className={`w-full max-w-[510px] h-24 p-6 bg-gradient-to-r rounded-2xl border-2 ${styles.gradient} ${styles.border} flex flex-col justify-start items-start`}>
      <div className="self-stretch h-12 flex justify-between items-center">
        <div className="flex justify-start items-center gap-3">
          <div className="pr-3 flex justify-start items-start">
            <div className="w-8 h-8 flex justify-center items-center">
              <Icon className={`w-8 h-8 ${styles.icon}`} strokeWidth={2.5} />
            </div>
          </div>
          <div className="flex justify-start items-center">
            <div className="text-slate-700 text-2xl md:text-3xl font-semibold leading-9">
              {title}
            </div>
          </div>
        </div>
        <div className="px-4 py-2 bg-white/50 rounded-full flex justify-start items-center">
          <div className={`${styles.text} text-2xl md:text-3xl font-bold leading-9`}>
            {status}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DetailedEvaluationItemCard;




