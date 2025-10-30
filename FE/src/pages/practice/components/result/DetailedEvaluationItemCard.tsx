import React from "react";

export type DetailedEvaluationItem = {
  id: string;
  title: string;
  score: number;
  icon: React.ElementType;
  colorVariant: "green" | "blue" | "amber";
};

const colorStyles = {
  green: {
    gradient: "from-green-50 to-green-100",
    border: "border-green-200",
    text: "text-green-600",
  },
  blue: {
    gradient: "from-blue-50 to-blue-100",
    border: "border-blue-200",
    text: "text-blue-600",
  },
  amber: {
    gradient: "from-orange-50 to-orange-100",
    border: "border-amber-200",
    text: "text-amber-600",
  },
};

type Props = {
  item: DetailedEvaluationItem;
};

const DetailedEvaluationItemCard: React.FC<Props> = ({ item }) => {
  const { title, score, icon: Icon, colorVariant } = item;
  const styles = colorStyles[colorVariant as keyof typeof colorStyles];

  return (
    <div className={`w-full rounded-2xl border bg-gradient-to-r p-5 shadow-sm ${styles.gradient} ${styles.border}`}>
      <div className="flex flex-row items-center justify-between space-y-0">
        <div className="flex items-center gap-3">
          <div className={`flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full ${styles.text}`}>
            <Icon className="h-7 w-7" />
          </div>
          <h2 className="text-xl font-semibold text-slate-700 sm:text-2xl">{title}</h2>
        </div>
        <div className="rounded-full bg-white/50 px-4 py-1.5">
          <span className={`text-lg font-bold sm:text-xl ${styles.text}`}>{score}점</span>
        </div>
      </div>
    </div>
  );
};

export default DetailedEvaluationItemCard;


