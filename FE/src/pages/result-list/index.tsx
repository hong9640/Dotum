import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import ResultHeader from './components/ResultHeader';
import AverageScoreCard from './components/AverageScoreCard';
import WordResultsList from './components/WordResultsList';
import ActionButtons from './components/ActionButtons';
import type { WordResult } from './types';
import { getSessionDetail } from '@/api/result-list/sessionDetailSearch';
import { useTrainingSession } from '@/hooks/training-session';
import { retryTrainingSession } from '@/api/training-session/sessionRetry';

// 날짜 포맷팅 함수
const formatDate = (dateString: string): string => {
  try {
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const dateHours = date.getHours();
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const ampm = dateHours < 12 ? '오전' : '오후';
    const displayHours = dateHours % 12 || 12;
    
    return `${year}년 ${month}월 ${day}일 ${ampm} ${displayHours}:${minutes} 완료`;
  } catch (error) {
    console.error('날짜 포맷팅 실패:', error);
    return '날짜 정보 없음';
  }
};

const WordSetResults: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [resultsData, setResultsData] = useState<WordResult[]>([]);
  const [sessionType, setSessionType] = useState<'word' | 'sentence'>('word');
  const [formattedDate, setFormattedDate] = useState<string>('');
  const [totalScore, setTotalScore] = useState<number>(0);
  const [overallFeedback, setOverallFeedback] = useState<string>('피드백 정보가 없습니다.');
  
  // 훈련 세션 훅 사용 (새로운 훈련 시작 시 사용)
  const { createWordSession, createSentenceSession } = useTrainingSession();
  
  // URL 파라미터에서 sessionId, type, date 가져오기
  const sessionIdParam = searchParams.get('sessionId');
  const typeParam = searchParams.get('type') as 'word' | 'sentence' | null;
  const dateParam = searchParams.get('date'); // training-history에서 온 경우 날짜 파라미터

  // 세션 상세 조회 API 호출
  useEffect(() => {
    const loadSessionDetail = async () => {
      if (!sessionIdParam || !typeParam) {
        setError('세션 정보가 없습니다. 홈페이지에서 다시 시작해주세요.');
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        setError(null);
        
        const sessionId = Number(sessionIdParam);
        if (isNaN(sessionId)) {
          setError('세션 ID가 유효하지 않습니다.');
          setIsLoading(false);
          return;
        }
        
        console.log('세션 상세 조회 시작:', { sessionId, type: typeParam });
        
        // 훈련 세션 상세 조회 API 호출
        const sessionDetailData = await getSessionDetail(sessionId);
        
        console.log('세션 상세 조회 성공:', sessionDetailData);
        
        // 세션 타입 설정
        setSessionType(sessionDetailData.type);
        
        // 날짜 포맷팅
        const formatted = formatDate(sessionDetailData.training_date);
        setFormattedDate(formatted);
        
        // training_items에서 완료된 아이템만 필터링하여 WordResult로 변환
        const completedItems = sessionDetailData.training_items?.filter(
          (item) => item.is_completed
        ) ?? [];
        
        const wordResults: WordResult[] = completedItems.map((item) => {
          // word 또는 sentence 필드에서 텍스트 가져오기
          const text = item.word || item.sentence || '';
          
          return {
            id: item.item_index + 1, // 1부터 시작하는 ID
            word: text,
            feedback: item.feedback || '피드백 정보가 없습니다.',
            score: item.score ?? 0, // score가 null이면 0으로 설정
          };
        });
        
        setResultsData(wordResults);
        
        // 전체 평균 점수 설정 (백엔드에서 제공하는 average_score 사용, null이면 0)
        setTotalScore(sessionDetailData.average_score ?? 0);
        
        // 전체 피드백 설정 (백엔드에서 제공하는 overall_feedback 사용, null이면 기본 메시지)
        setOverallFeedback(sessionDetailData.overall_feedback || '피드백 정보가 없습니다.');
        
        setIsLoading(false);
      } catch (err: any) {
        console.error('세션 상세 조회 실패:', err);
        
        let errorMessage = '세션 상세 조회에 실패했습니다.';
        if (err.status === 401) {
          errorMessage = '인증이 필요합니다. 다시 로그인해주세요.';
        } else if (err.status === 404) {
          errorMessage = '세션을 찾을 수 없습니다.';
        } else if (err.message) {
          errorMessage = err.message;
        }
        
        setError(errorMessage);
        setIsLoading(false);
      }
    };

    loadSessionDetail();
  }, [sessionIdParam, typeParam]);

  // 로딩 상태
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-lg text-gray-600">결과 데이터를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  // 에러 상태
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-6">
          <div className="text-6xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">오류 발생</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <button 
            onClick={() => navigate('/')}
            className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            홈으로 돌아가기
          </button>
        </div>
      </div>
    );
  }

  // 데이터가 없는 경우 처리
  if (resultsData.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-6">
          <div className="text-6xl mb-4">📊</div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">결과 데이터가 없습니다</h2>
          <p className="text-gray-600 mb-6">
            아직 완료된 훈련 결과가 없습니다.<br />
            훈련을 완료한 후 다시 확인해주세요.
          </p>
          <button 
            onClick={() => navigate('/')}
            className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            홈으로 돌아가기
          </button>
        </div>
      </div>
    );
  }

  const handleBack = () => {
    // date 파라미터가 있으면 training-history 페이지로 이동, 없으면 홈으로 이동
    if (dateParam) {
      navigate(`/training-history?date=${dateParam}`);
    } else {
      navigate('/'); // 홈으로 이동
    }
  };

  const handleDetailClick = (result: WordResult) => {
    // result-detail 페이지로 이동 (URL 파라미터로 sessionId, type, itemIndex 전달)
    if (sessionIdParam && typeParam) {
      // result.id는 1부터 시작, itemIndex는 0부터 시작하므로 -1 필요
      let detailUrl = `/result-detail?sessionId=${sessionIdParam}&type=${typeParam}&itemIndex=${result.id - 1}`;
      // date 파라미터가 있으면 함께 전달
      if (dateParam) {
        detailUrl += `&date=${dateParam}`;
      }
      navigate(detailUrl);
    } else {
      console.error('세션 정보가 없습니다.');
      alert('세션 정보를 찾을 수 없습니다.');
    }
  };

  const handleRetry = async () => {
    if (!sessionIdParam) {
      console.error('세션 ID가 없습니다.');
      alert('세션 정보를 찾을 수 없습니다.');
      return;
    }

    try {
      const sessionId = Number(sessionIdParam);
      if (isNaN(sessionId)) {
        alert('유효하지 않은 세션 ID입니다.');
        return;
      }

      console.log('재훈련 세션 생성 시작:', { sessionId });
      
      // 재훈련 API 호출
      const retrySession = await retryTrainingSession(sessionId);
      
      console.log('재훈련 세션 생성 성공:', retrySession);
      
      // 성공 시 practice 페이지로 이동 (sessionId, type, itemIndex=0)
      if (retrySession.session_id && retrySession.type) {
        navigate(`/practice?sessionId=${retrySession.session_id}&type=${retrySession.type}&itemIndex=0`);
      } else {
        alert('재훈련 세션 정보가 올바르지 않습니다.');
      }
    } catch (error: any) {
      console.error('재훈련 세션 생성 실패:', error);
      alert(error.message || '재훈련 세션 생성에 실패했습니다.');
    }
  };

  const handleNewTraining = async () => {
    // 현재 세션의 훈련 타입에 따라 단어 또는 문장 세션 생성
    try {
      if (sessionType === 'word') {
        // 단어 연습 시작과 동일하게 동작
        await createWordSession(2);
      } else {
        // 문장 연습 시작과 동일하게 동작
        await createSentenceSession(2);
      }
    } catch (error) {
      // 에러는 훅에서 처리됨 (toast 메시지 표시)
      console.error('새로운 훈련 세션 생성 실패:', error);
    }
  };

  return (
    <div className="self-stretch pt-7 pb-10 flex flex-col justify-start items-center bg-slate-50 min-h-screen">
      
      {/* 헤더 */}
      <ResultHeader
        type={sessionType}
        date={formattedDate}
        onBack={handleBack}
      />

      {/* 메인 콘텐츠 영역 */}
      <div className="p-4 md:p-8 flex flex-col justify-start items-center gap-8 w-full">
        
        {/* 전체 평균 점수 카드 */}
        <AverageScoreCard
          totalScore={totalScore}
          feedback={overallFeedback}
        />
        
        {/* 단어별 결과 목록 */}
        <WordResultsList
          results={resultsData}
          onDetailClick={handleDetailClick}
        />
        
        {/* 다음 행동 버튼 */}
        <ActionButtons
          onRetry={handleRetry}
          onNewTraining={handleNewTraining}
        />
      </div>
    </div>
  );
};

export default WordSetResults;
