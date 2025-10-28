import type { TrainingSet } from './types';
import { Header, TrainingSetGrid } from './components';
import { generateSampleData } from './utils';
import { useTrainingDayDetail } from '@/hooks/useTrainingDayDetail';

export interface TrainingDayDetailProps {
  date: string; // "YYYY-MM-DD" 형식
  trainingSets?: TrainingSet[];
  onBack?: () => void;
  onTrainingSetClick?: (trainingSet: TrainingSet) => void;
}

export default function TrainingDayDetail({ 
  date, 
  trainingSets, 
  onBack,
  onTrainingSetClick 
}: TrainingDayDetailProps) {
  // API에서 받아온 trainingSets 사용 (없으면 더미 데이터 생성)
  const actualTrainingSets = trainingSets || generateSampleData(6, date);
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
