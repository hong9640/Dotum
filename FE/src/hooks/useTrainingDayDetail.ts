import { useState, useMemo } from 'react';
import type { TrainingSet } from '@/pages/training-history-detail/types';

interface UseTrainingDayDetailProps {
  trainingSets: TrainingSet[];
}

export function useTrainingDayDetail({ trainingSets }: UseTrainingDayDetailProps) {
  const [selectedTrainingSet, setSelectedTrainingSet] = useState<TrainingSet | null>(null);

  const statistics = useMemo(() => {
    const totalSets = trainingSets.length;
    const averageScore = totalSets > 0 
      ? Math.round(trainingSets.reduce((sum, set) => sum + set.score, 0) / totalSets)
      : 0;
    const totalWords = trainingSets.reduce((sum, set) => sum + set.words.length, 0);

    return {
      totalSets,
      averageScore,
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
