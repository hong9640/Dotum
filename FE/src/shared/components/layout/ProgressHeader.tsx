import React from "react";
import { Progress } from "@/shared/components/ui/progress";

interface ProgressHeaderProps {
  step: number;
  totalSteps: number;
  title?: string;
}

const ProgressHeader: React.FC<ProgressHeaderProps> = ({
  step,
  totalSteps,
  title = "진행률"
}) => {
  const progressPct = Math.min(100, Math.max(0, (step / totalSteps) * 100));

  return (
    <div>
      <div className="flex items-center justify-between">
        <h2 className="text-slate-800 text-2xl sm:text-3xl font-semibold">{title}</h2>
        <span className="text-green-600 text-xl sm:text-3xl font-semibold">{step} / {totalSteps}</span>
      </div>
      <Progress value={progressPct} className="mt-4 h-3 bg-slate-100 [&>div]:bg-green-500" />
    </div>
  );
};

export default ProgressHeader;
