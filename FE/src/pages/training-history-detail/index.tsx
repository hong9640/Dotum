import type { TrainingSet } from './types';
import { Header, TrainingSetGrid } from './components';
import { generateSampleData } from './utils';
import { useTrainingDayDetail } from '@/hooks/useTrainingDayDetail';

export interface TrainingDayDetailProps {
  date: string; // "YYYY-MM-DD" 형식
  trainingSets?: TrainingSet[];
  expectedCount?: number; // 달력에서 전달받은 예상 학습 횟수
  onBack?: () => void;
  onTrainingSetClick?: (trainingSet: TrainingSet) => void;
}


export default function TrainingDayDetail({ 
  date, 
  trainingSets, 
  expectedCount = 6, // 기본값 6개
  onBack,
  onTrainingSetClick 
}: TrainingDayDetailProps) {
  // trainingSets가 없으면 expectedCount를 기반으로 동적 생성
  const actualTrainingSets = trainingSets || generateSampleData(expectedCount, date);
  const { statistics } = useTrainingDayDetail({ trainingSets: actualTrainingSets });

  const handleTrainingSetClick = (trainingSet: TrainingSet) => {
    if (onTrainingSetClick) {
      onTrainingSetClick(trainingSet);
    }
  };

  return (
    <div className="min-h-screen w-full bg-slate-50">
      <Header 
        date={date} 
        totalSets={statistics.totalSets} 
        onBack={onBack} 
      />
      
      <main className="container mx-auto px-6 xl:px-8 py-8">
        <div className="max-w-4xl mx-auto space-y-6">
          <div className="space-y-4">
            <TrainingSetGrid 
              trainingSets={actualTrainingSets}
              onTrainingSetClick={handleTrainingSetClick}
            />
          </div>
        </div>
      </main>
    </div>
  );
}

// Export types and components
export * from './types';
export * from './components';
