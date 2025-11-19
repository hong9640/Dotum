import React from "react";
import { Button } from "@/shared/components/ui/button";
import { RotateCcw, ListChecks, Loader2, ArrowRight } from "lucide-react";

interface ActionButtonsProps {
  onRetake?: () => void;
  onViewAllResults?: () => void;
  onNext?: () => void;
  hasNext?: boolean;
  isCompletingSession?: boolean;
  onBack?: () => void; // result-detail 페이지용 맨 위로 버튼 표시 여부 (실제 동작은 페이지 상단 스크롤)
  isUploading?: boolean;
}

/**
 * 결과 페이지 하단 액션 버튼 컴포넌트
 */
const ActionButtons: React.FC<ActionButtonsProps> = ({
  onRetake,
  onViewAllResults,
  onNext,
  hasNext = false,
  isCompletingSession = false,
  onBack,
  isUploading = false,
}) => {
  const handleNextWord = () => {
    if (onNext) {
      onNext();
    }
  };

  // onBack이 있으면 아무것도 렌더링하지 않음 (result-detail 페이지용)
  if (onBack) {
    return null;
  }

  // 버튼이 하나도 없으면 렌더링하지 않음
  if (!onRetake && !onViewAllResults && !onNext) {
    return null;
  }

  return (
    <div className="self-stretch pt-6 inline-flex justify-center items-start">
      <div className="flex-1 pt-8 flex justify-center items-center gap-6 flex-wrap content-center">
        {/* 다시 녹화 버튼 - 항상 표시 */}
        {onRetake && (
          <Button
            variant="outline"
            size="lg"
            onClick={onRetake}
            disabled={isCompletingSession || isUploading}
            className="w-full md:w-auto h-auto min-h-10 px-6 py-4 bg-white text-slate-700 border-slate-200 border-2 hover:bg-slate-100 hover:text-slate-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl text-xl md:text-3xl font-semibold leading-9"
          >
            <RotateCcw className="w-8 h-8 mr-2" strokeWidth={2.5} />
            다시 녹화
          </Button>
        )}

        {/* 마지막 아이템인 경우: 전체 결과 보기 버튼 표시 */}
        {!hasNext && onViewAllResults ? (
          <Button
            variant="default"
            size="lg"
            onClick={onViewAllResults}
            disabled={isCompletingSession}
            className="w-full md:w-auto h-auto min-h-10 px-6 py-4 bg-blue-500 text-white hover:bg-blue-600 disabled:bg-blue-300 disabled:cursor-not-allowed rounded-xl text-xl md:text-3xl font-semibold leading-9"
          >
            {isCompletingSession ? (
              <>
                <Loader2 className="w-8 h-8 mr-2 animate-spin" strokeWidth={3} />
                세션 완료 중...
              </>
            ) : (
              <>
                <ListChecks className="w-8 h-8 mr-2" strokeWidth={3} />
                전체 결과 보기
              </>
            )}
          </Button>
        ) : hasNext && onNext ? (
          /* 마지막 아이템이 아닌 경우: 다음으로 버튼 표시 */
          <Button
            variant="default"
            size="lg"
            onClick={handleNextWord}
            disabled={isUploading}
            className="w-full md:w-auto h-auto min-h-10 px-6 py-4 bg-green-500 text-white hover:bg-green-600 disabled:bg-gray-400 disabled:cursor-not-allowed rounded-xl text-xl md:text-3xl font-semibold leading-9"
          >
            <ArrowRight className="w-8 h-8 mr-2" strokeWidth={3} />
            다음으로
          </Button>
        ) : null}
      </div>
    </div>
  );
};

export default ActionButtons;
export type { ActionButtonsProps };
