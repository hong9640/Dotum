import type { TrainingSet } from '../types';
import { Header, TrainingSetGrid } from '../components/detail';
import { useTrainingHistoryDetail } from '../hooks';

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
  // 모든 비즈니스 로직을 훅으로 분리
  const {
    actualTrainingSets,
    isLoading,
    error,
    totalSessions,
    statistics,
    handleTrainingSetClick,
  } = useTrainingHistoryDetail({ date, trainingSets });

  // totalSets는 API 응답의 total_sessions를 우선 사용
  const displayTotalSets = totalSessions > 0 ? totalSessions : statistics.totalSets;

  // onTrainingSetClick이 있으면 래핑
  const wrappedHandleTrainingSetClick = async (trainingSet: TrainingSet) => {
    await handleTrainingSetClick(trainingSet);
    if (onTrainingSetClick) {
      onTrainingSetClick(trainingSet);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen w-full flex items-center justify-center">
        <div className="text-lg text-gray-600">로딩 중...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen w-full flex items-center justify-center">
        <div className="text-lg text-red-600">에러: {error}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen w-full flex flex-col items-center" >
      <div className="container flex justify-center mx-auto px-6 xl:px-8 pt-8 pb-0 sm-pb-5 ">
        <Header
          date={date}
          totalSets={displayTotalSets}
          onBack={onBack}
        />
      </div>

      <main className="container mx-auto px-6 xl:px-8 py-2.5 sm:py-8">
        <div className="max-w-4xl mx-auto space-y-6">
          <div className="space-y-4">
            <TrainingSetGrid
              trainingSets={actualTrainingSets}
              onTrainingSetClick={wrappedHandleTrainingSetClick}
            />
          </div>
        </div>
      </main>
    </div>
  );
}

