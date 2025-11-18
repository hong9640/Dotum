import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/card';
import type { TrainingSet } from '@/features/training-history/types';
import { ScoreChip } from './ScoreChip';
import { WordChip } from './WordChip';
import { formatDateTime } from '@/shared/utils/dateFormatter';

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
        w-full h-[144.8px] sm:h-[163px] cursor-pointer transition-all duration-200
        hover:shadow-md hover:scale-[1.02] active:scale-[0.98]
        border-gray-200 hover:border-gray-300
        ${onClick ? 'hover:bg-slate-50' : ''}
      `}
      onClick={handleClick}
    >
      <CardHeader className="pb-3 sm:pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg sm:text-xl font-semibold text-gray-900">
            {trainingSet.title}
          </CardTitle>
          <ScoreChip score={trainingSet.score} />
        </div>
      </CardHeader>
      
      <CardContent className="pt-0">
        <div className="space-y-3 sm:space-y-4">
          <div>
            <h4 className={`text-sm sm:text-base font-medium text-gray-600 mb-2 sm:mb-2.5 ${trainingSet.type === 'vocal' ? 'invisible' : ''}`}>
              {trainingSet.type === 'word' ? '연습한 단어' : trainingSet.type === 'vocal' ? '발성 연습' : '연습한 문장'} ({trainingSet.totalItems}개 중 {Math.min(trainingSet.words.length, trainingSet.totalItems)}개 표시):
            </h4>
            <div className="flex flex-wrap gap-2 sm:gap-2.5">
              {trainingSet.words.length > 0 ? (
                trainingSet.words.map((word, index) => (
                  <WordChip 
                    key={`${word}-${index}`} 
                    word={word} 
                    isSentence={trainingSet.type === 'sentence' || trainingSet.type === 'vocal'}
                  />
                ))
              ) : (
                <span className="text-sm sm:text-base text-gray-500">
                {trainingSet.type === 'vocal' && trainingSet.created_at 
                  ? `연습일: ${formatDateTime(trainingSet.created_at)}`
                  : '표시할 항목이 없습니다.'}
                </span>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
