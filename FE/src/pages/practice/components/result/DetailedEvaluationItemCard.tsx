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
    text: "text-green-500",
  },
  blue: {
    gradient: "from-blue-50 to-blue-100",
    border: "border-blue-200",
    text: "text-blue-500",
  },
  amber: {
    gradient: "from-orange-50 to-orange-100",
    border: "border-amber-200",
    text: "text-amber-500",
  },
};

type Props = {
  item: DetailedEvaluationItem;
};

const DetailedEvaluationItemCard: React.FC<Props> = ({ item }) => {
  const { title, score, icon: Icon, colorVariant } = item;
  const styles = colorStyles[colorVariant as keyof typeof colorStyles];

  return (
    <div className={`w-full max-w-[510px] h-24 p-6 bg-gradient-to-r rounded-2xl border-2 ${styles.gradient} ${styles.border} flex flex-col justify-start items-start`}>
      <div className="self-stretch h-12 flex justify-between items-center">
        <div className="flex justify-start items-center gap-3">
          <div className="pr-3 flex justify-start items-start">
            <div className="w-8 h-8 flex justify-center items-center">
              <Icon className={`w-8 h-8 ${styles.text}`} strokeWidth={2.5} />
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
            {score}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DetailedEvaluationItemCard;


