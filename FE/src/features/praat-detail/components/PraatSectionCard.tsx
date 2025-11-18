import React from "react";
import { Card, CardContent, CardHeader } from "@/shared/components/ui/card";

export type PraatSectionCardProps = {
  title: string;
  titleIconClass?: string; // 작은 색 블록용
  children: React.ReactNode;
  className?: string;
};

/**
 * Praat 섹션 카드 래퍼 컴포넌트
 */
const PraatSectionCard: React.FC<PraatSectionCardProps> = ({
  title,
  titleIconClass,
  children,
  className,
}) => {
  return (
    <Card
      className={`rounded-2xl shadow-sm border-gray-200 ${className ?? ""}`}
    >
      <CardHeader className="pb-6">
        <div className="flex items-center">
          {titleIconClass ? (
            <span className="pr-3 flex items-center">
              <span className="relative flex items-center w-5 h-8">
                <span className="w-5 h-5 left-0 top-[6px] absolute overflow-hidden">
                  <span className={`absolute left-[2.85px] top-[0.83px] block ${titleIconClass}`} />
                </span>
              </span>
            </span>
          ) : null}
          <h3 className="text-gray-900 text-lg sm:text-xl font-semibold leading-8">{title}</h3>
        </div>
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
};

export default PraatSectionCard;

