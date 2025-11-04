import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import ResultHeader from './components/ResultHeader';
import AverageScoreCard from './components/AverageScoreCard';
import WordResultsList from './components/WordResultsList';
import ActionButtons from './components/ActionButtons';
import type { WordResult } from './types';
import { getSessionDetail } from '@/api/result-list/sessionDetailSearch';
import { generateDummyWordResults } from './utils';
import { useTrainingSession } from '@/hooks/training-session';

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
  
  // 훈련 세션 훅 사용 (새로운 훈련 시작 시 사용)
  const { createWordSession, createSentenceSession } = useTrainingSession();
  
  // URL 파라미터에서 sessionId와 type 가져오기
  const sessionIdParam = searchParams.get('sessionId');
  const typeParam = searchParams.get('type') as 'word' | 'sentence' | null;

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
        
        // 더미데이터 생성 (completed_items와 total_items 중 큰 값 사용, 최소 10개)
        const dataCount = Math.max(sessionDetailData.completed_items, 10);
        const dummyResults = generateDummyWordResults(dataCount);
        
        // completed_items만큼 slice
        const slicedResults = dummyResults.slice(0, sessionDetailData.completed_items);
        setResultsData(slicedResults);
        
        // 전체 평균 점수 계산
        const avgScore = slicedResults.length > 0
          ? Math.round(slicedResults.reduce((acc, r) => acc + r.score, 0) / slicedResults.length)
          : 0;
        setTotalScore(avgScore);
        
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
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
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
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
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
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
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
    navigate('/'); // 홈으로 이동
  };

  const handleDetailClick = (result: WordResult) => {
    // TODO: 상세 결과 페이지로 이동
    console.log("상세 결과 보기:", result);
    navigate(`/result-detail/${result.id}`);
  };

  const handleRetry = () => {
    // TODO: 다시 연습하기 로직
    console.log("다시 연습하기");
    navigate('/practice');
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
          feedback="아주 잘했어요. 조금만 더 연습하면 완벽해질 것 같아요."
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
