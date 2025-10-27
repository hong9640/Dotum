import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { TrainingSet } from '../types';
import { ScoreChip } from './ScoreChip';
import { WordChip } from './WordChip';

interface TrainingSetCardProps {
  trainingSet: TrainingSet;
  onClick?: (trainingSet: TrainingSet) => void;
}

export function TrainingSetCard({ trainingSet, onClick }: TrainingSetCardProps) {
  const handleClick = () => {
    if (onClick) {
      onClick(trainingSet);
    }
  };

  return (
    <Card 
      className={`
        w-full cursor-pointer transition-all duration-200
        hover:shadow-md hover:scale-[1.02] active:scale-[0.98]
        border-gray-200 hover:border-gray-300
        ${onClick ? 'hover:bg-gray-50' : ''}
      `}
      onClick={handleClick}
    >
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold text-gray-900">
            {trainingSet.title}
          </CardTitle>
          <ScoreChip score={trainingSet.score} />
        </div>
      </CardHeader>
      
      <CardContent className="pt-0">
        <div className="space-y-3">
          <div>
            <h4 className="text-sm font-medium text-gray-600 mb-2">
              연습한 단어 (10개 중 3개 표시):
            </h4>
            <div className="flex flex-wrap gap-2">
              {trainingSet.words.map((word, index) => (
                <WordChip key={`${word}-${index}`} word={word} />
              ))}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
