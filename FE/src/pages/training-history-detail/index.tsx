import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import type { TrainingSet } from './types';
import { Header, TrainingSetGrid } from './components';
import { convertSessionsToTrainingSets } from './utils';
import { useTrainingDayDetail } from '@/hooks/useTrainingDayDetail';
import { getDailyRecordSearch } from '@/api/training-history/dailyRecordSearch';
import { completeTrainingSession } from '@/api/training-session';
import { toast } from 'sonner';

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
  const navigate = useNavigate();
  const [actualTrainingSets, setActualTrainingSets] = useState<TrainingSet[]>(trainingSets || []);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [totalSessions, setTotalSessions] = useState<number>(0);
  const [isCompleting, setIsCompleting] = useState(false);

  const { statistics } = useTrainingDayDetail({ trainingSets: actualTrainingSets });

  // API 호출
  useEffect(() => {
    // props로 trainingSets가 전달된 경우 API 호출하지 않음
    if (trainingSets !== undefined) {
      setActualTrainingSets(trainingSets);
      return;
    }

    // date가 없으면 처리하지 않음
    if (!date) {
      return;
    }

    const fetchDailyRecords = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await getDailyRecordSearch(date);

        // API 응답을 TrainingSet 배열로 변환
        const convertedSets = convertSessionsToTrainingSets(response);
        setActualTrainingSets(convertedSets);
        setTotalSessions(response.total_sessions);
      } catch (err: unknown) {
        console.error('일별 훈련 기록 조회 실패 :', err);
        const axiosError = err as { response?: { data?: { detail?: string } } };
        setError(axiosError.response?.data?.detail || '훈련 기록을 불러오는데 실패했습니다.');
        // 에러 발생 시 빈 배열 또는 더미 데이터 사용
        setActualTrainingSets([]);
        setTotalSessions(0);
      } finally {
        setIsLoading(false);
      }
    };

    fetchDailyRecords();
  }, [date, trainingSets]);

  // 날짜를 YYYYMMDD 형식으로 변환하는 함수
  const formatDateForUrl = (dateString: string): string => {
    // YYYY-MM-DD 형식이면 YYYYMMDD로 변환
    if (dateString.includes('-')) {
      return dateString.replace(/-/g, '');
    }
    return dateString;
  };

  const handleTrainingSetClick = async (trainingSet: TrainingSet) => {
    // 이미 세션 완료 처리 중이면 중복 실행 방지
    if (isCompleting) return;
    
    // 세션이 완료되지 않은 경우
    if (trainingSet.status !== 'completed') {
      // 총 아이템 수와 완료된 아이템 수가 같은 경우 (실제로는 완료되었지만 status가 in_progress인 경우)
      if (trainingSet.completedItems !== undefined && trainingSet.totalItems === trainingSet.completedItems) {
        try {
          setIsCompleting(true);
          
          // 세션 종료 API 호출
          await completeTrainingSession(trainingSet.sessionId);

          // result-list 페이지로 이동
          const dateParam = formatDateForUrl(date);
          navigate(`/result-list?sessionId=${trainingSet.sessionId}&type=${trainingSet.type}&date=${dateParam}`);

          // 부모 컴포넌트에서 전달받은 onClick 핸들러가 있으면 호출
          if (onTrainingSetClick) {
            onTrainingSetClick(trainingSet);
          }
        } catch (error: unknown) {
          console.error('세션 종료 실패:', error);
          const errorWithMessage = error as { message?: string };
          toast.error(errorWithMessage.message || '세션을 종료하는데 실패했습니다.');
          setIsCompleting(false);
        }
        return;
      }

      // 총 아이템 수와 완료된 아이템 수가 다른 경우 (실제로 진행 중인 경우)
      const message = '아직 훈련이 완료되지 않았습니다.\n훈련을 이어서 진행할까요? 😊';
      const shouldNavigate = window.confirm(message); // 확인 버튼 클릭 시 true, 취소 버튼 클릭 시 false

      if (shouldNavigate) {
        // vocal 타입인 경우 특별한 경로 처리
        if (trainingSet.type === 'vocal' && trainingSet.currentItemIndex !== undefined && trainingSet.totalItems) {
          const n = Math.floor(trainingSet.totalItems / 5); // 반복 횟수
          const currentIndex = trainingSet.currentItemIndex;
          let path = '';
          let attempt = 1;

          if (currentIndex >= 0 && currentIndex < n) {
            // 0 ~ n-1: /voice-training/mpt
            path = '/voice-training/mpt';
            attempt = currentIndex + 1;
          } else if (currentIndex >= n && currentIndex < 2 * n) {
            // n ~ 2n-1: /voice-training/crescendo
            path = '/voice-training/crescendo';
            attempt = currentIndex - n + 1;
          } else if (currentIndex >= 2 * n && currentIndex < 3 * n) {
            // 2n ~ 3n-1: /voice-training/decrescendo
            path = '/voice-training/decrescendo';
            attempt = currentIndex - 2 * n + 1;
          } else if (currentIndex >= 3 * n && currentIndex < 4 * n) {
            // 3n ~ 4n-1: /voice-training/loud-soft
            path = '/voice-training/loud-soft';
            attempt = currentIndex - 3 * n + 1;
          } else if (currentIndex >= 4 * n && currentIndex < 5 * n) {
            // 4n ~ 5n-1: /voice-training/soft-loud
            path = '/voice-training/soft-loud';
            attempt = currentIndex - 4 * n + 1;
          } else {
            // 범위를 벗어난 경우 기본 practice 페이지로 이동
            navigate(`/practice?sessionId=${trainingSet.sessionId}&type=${trainingSet.type}&itemIndex=${trainingSet.currentItemIndex}`);
            return;
          }

          navigate(`${path}?attempt=${attempt}&sessionId=${trainingSet.sessionId}`);
        } else {
          // vocal이 아니거나 필요한 정보가 없는 경우 기존 로직 사용
          navigate(`/practice?sessionId=${trainingSet.sessionId}&type=${trainingSet.type}&itemIndex=${trainingSet.currentItemIndex}`);
        }
      }
      return;
    }

    // 완료된 세션은 result-list 페이지로 이동 (date 파라미터도 함께 전달)
    const dateParam = formatDateForUrl(date);
    navigate(`/result-list?sessionId=${trainingSet.sessionId}&type=${trainingSet.type}&date=${dateParam}`);

    // 부모 컴포넌트에서 전달받은 onClick 핸들러가 있으면 호출
    if (onTrainingSetClick) {
      onTrainingSetClick(trainingSet);
    }
  };

  // totalSets는 API 응답의 total_sessions를 우선 사용
  const displayTotalSets = totalSessions > 0 ? totalSessions : statistics.totalSets;

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
