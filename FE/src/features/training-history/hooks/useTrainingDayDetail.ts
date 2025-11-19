import { useState, useMemo } from 'react';
import type { TrainingSet } from '@/features/training-history/types';

interface UseTrainingDayDetailProps {
  trainingSets: TrainingSet[];
}

export function useTrainingDayDetail({ trainingSets }: UseTrainingDayDetailProps) {
  const [selectedTrainingSet, setSelectedTrainingSet] = useState<TrainingSet | null>(null);

  const statistics = useMemo(() => {
    const totalSets = trainingSets.length;
    const totalWords = trainingSets.reduce((sum, set) => sum + set.words.length, 0);

    return {
      totalSets,
      totalWords
    };
  }, [trainingSets]);

  const handleTrainingSetClick = (trainingSet: TrainingSet) => {
    setSelectedTrainingSet(trainingSet);
  };

  const handleCloseDetail = () => {
    setSelectedTrainingSet(null);
  };

  return {
    selectedTrainingSet,
    statistics,
    handleTrainingSetClick,
    handleCloseDetail
  };
}
