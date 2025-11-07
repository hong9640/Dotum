import React from "react";

type MaybeNum = number | null | undefined;

export type MetricTileProps = {
  title: string;
  value: MaybeNum;
  unit?: string;
  normalText: string;
  status: React.ReactNode;
  className?: string;
};

/**
 * Praat 지표 타일 컴포넌트
 */
const PraatMetricTile: React.FC<MetricTileProps> = ({
  title,
  value,
  unit,
  normalText,
  status,
  className,
}) => {
  // 값이 없으면 0으로 처리
  const v = value ?? 0;

  return (
    <div
      className={`rounded-xl outline outline-1 outline-offset-[-1px] outline-gray-200 p-4 flex flex-col ${
        className ?? ""
      }`}
    >
      <div className="pb-2">
        <div className="flex items-center justify-between gap-2">
          <div className="text-gray-900 text-sm sm:text-base font-medium break-words flex-1 min-w-0">{title}</div>
          <div className="flex-shrink-0">{status}</div>
        </div>
      </div>
      <div>
        <div className="flex items-center gap-2 flex-wrap">
          <div className="text-gray-900 text-xl sm:text-2xl font-bold leading-8 sm:leading-10">
            {v.toString()}
          </div>
          {unit ? (
            <div className="text-gray-500 text-xs sm:text-sm">{unit}</div>
          ) : null}
        </div>
        <div className="pt-1">
          <div className="text-gray-500 text-xs sm:text-sm">정상 범위: {normalText}</div>
        </div>
      </div>
    </div>
  );
};

export default PraatMetricTile;

