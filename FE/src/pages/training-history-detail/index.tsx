import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import type { TrainingSet } from './types';
import { Header, TrainingSetGrid } from './components';
import { convertSessionsToTrainingSets } from './utils';
import { useTrainingDayDetail } from '@/hooks/useTrainingDayDetail';
import { getDailyRecordSearch } from '@/api/training-history/dailyRecordSearch';

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
      } catch (err: any) {
        console.error('일별 훈련 기록 조회 실패 :', err);
        setError(err.response?.data?.detail || '훈련 기록을 불러오는데 실패했습니다.');
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

  const handleTrainingSetClick = (trainingSet: TrainingSet) => {
    // 세션이 완료되지 않은 경우
    if (trainingSet.status !== 'completed') {
      const message = '아직 훈련이 완료되지 않았습니다.\n훈련을 이어서 진행할까요? 😊';
      const shouldNavigate = window.confirm(message); // 확인 버튼 클릭 시 true, 취소 버튼 클릭 시 false
      
      if (shouldNavigate) {
        // practice 페이지로 이동 (current_item_index 사용)
        navigate(`/practice?sessionId=${trainingSet.sessionId}&type=${trainingSet.type}&itemIndex=${trainingSet.currentItemIndex}`);
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
  // totalSets는 API 응답의 total_sessions를 우선 사용
  const displayTotalSets = totalSessions > 0 ? totalSessions : statistics.totalSets;

  if (isLoading) {
    return (
      <div className="min-h-screen w-full bg-slate-50 flex items-center justify-center">
        <div className="text-lg text-gray-600">로딩 중...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen w-full bg-slate-50 flex items-center justify-center">
        <div className="text-lg text-red-600">에러: {error}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen w-full bg-slate-50">
      <Header 
        date={date} 
        totalSets={displayTotalSets} 
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
