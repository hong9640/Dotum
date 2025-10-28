import React from 'react';
import { getScoreLevel, scoreColorClasses } from '../types';

interface ScoreChipProps {
  score: number;
  className?: string;
}

export function ScoreChip({ score, className = '' }: ScoreChipProps) {
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
