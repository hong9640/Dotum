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
        ${onClick ? 'hover:bg-slate-50' : ''}
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
              {trainingSet.type === 'word' ? '연습한 단어' : '연습한 문장'} ({trainingSet.totalItems}개 중 {Math.min(trainingSet.words.length, trainingSet.totalItems)}개 표시):
            </h4>
            <div className="flex flex-wrap gap-2">
              {trainingSet.words.length > 0 ? (
                trainingSet.words.map((word, index) => (
                  <WordChip 
                    key={`${word}-${index}`} 
                    word={word} 
                    isSentence={trainingSet.type === 'sentence'}
                  />
                ))
              ) : (
                <span className="text-sm text-gray-500">표시할 항목이 없습니다.</span>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
