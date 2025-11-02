import { getScoreLevel, scoreColorClasses } from '../types';

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

  // 완료된 상태인 경우
  const level = getScoreLevel(score);
  const colors = scoreColorClasses[level];

  return (
    <div
      className={`
        inline-flex items-center px-2 py-1 rounded-full text-sm font-semibold
        ${colors.background} ${colors.border} ${colors.text}
        border
        ${className}
      `}
    >
      {score}점
    </div>
  );
}
