import { scoreColorClasses } from '@/features/training-history/types';

interface ScoreChipProps {
  score: number | null; // null은 진행중 상태
  className?: string;
}

export function ScoreChip({ score, className = '' }: ScoreChipProps) {
  // 진행중 상태인 경우
  if (score === null) {
    const colors = scoreColorClasses.in_progress;
    return (
      <div
        className={`
          inline-flex items-center px-2 py-1 rounded-full text-sm font-semibold
          ${colors.background} ${colors.border} ${colors.text}
          border
          ${className}
        `}
      >
        진행중
      </div>
    );
  }

  // 완료된 상태인 경우 - "완료"로 표시
  const colors = scoreColorClasses.high; // 완료 상태는 파란색 계열 사용

  return (
    <div
      className={`
        inline-flex items-center px-2 py-1 rounded-full text-sm font-semibold
        ${colors.background} ${colors.border} ${colors.text}
        border
        ${className}
      `}
    >
      완료
    </div>
  );
}
