import type { TrainingSet } from '../types';
import { TrainingSetCard } from './TrainingSetCard';
import { EmptyState } from './EmptyState';

interface TrainingSetGridProps {
  trainingSets: TrainingSet[];
  onTrainingSetClick?: (trainingSet: TrainingSet) => void;
}

export function TrainingSetGrid({ trainingSets, onTrainingSetClick }: TrainingSetGridProps) {
  if (trainingSets.length === 0) {
    return <EmptyState />;
  }

  return (
    <div className="grid grid-cols-2 gap-4">
      {trainingSets.map((trainingSet) => (
        <TrainingSetCard
          key={trainingSet.id}
          trainingSet={trainingSet}
          onClick={onTrainingSetClick}
        />
      ))}
    </div>
  );
}
