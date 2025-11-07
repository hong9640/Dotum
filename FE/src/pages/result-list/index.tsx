import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import ResultHeader from './components/ResultHeader';
import WordResultsList from './components/WordResultsList';
import ActionButtons from './components/ActionButtons';
import type { WordResult } from './types';
import { getSessionDetail } from '@/api/result-list/sessionDetailSearch';
import { useTrainingSession } from '@/hooks/training-session';
import { retryTrainingSession } from '@/api/training-session/sessionRetry';
import 도드미치료사 from "@/assets/도드미_치료사.png";

// 날짜 포맷팅 함수 (시간 제외)
const formatDate = (dateString: string): string => {
  try {
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    
    return `${year}년 ${month}월 ${day}일 완료`;
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
  const [sessionType, setSessionType] = useState<'word' | 'sentence' | 'vocal'>('word');
  const [formattedDate, setFormattedDate] = useState<string>('');
  const [cpp, setCpp] = useState<number | null>(null);
  const [csid, setCsid] = useState<number | null>(null);
  // 발성 연습 메트릭
  const [jitter, setJitter] = useState<number | null>(null);
  const [shimmer, setShimmer] = useState<number | null>(null);
  const [nhr, setNhr] = useState<number | null>(null);
  const [hnr, setHnr] = useState<number | null>(null);
  const [maxF0, setMaxF0] = useState<number | null>(null);
  const [minF0, setMinF0] = useState<number | null>(null);
  const [lhRatioMeanDb, setLhRatioMeanDb] = useState<number | null>(null);
  const [lhRatioSdDb, setLhRatioSdDb] = useState<number | null>(null);
  const [isVoiceTraining, setIsVoiceTraining] = useState<boolean>(false);
  const [_overallFeedback, setOverallFeedback] = useState<string>('피드백 정보가 없습니다.');
  
  // 훈련 세션 훅 사용 (새로운 훈련 시작 시 사용)
  const { createWordSession, createSentenceSession } = useTrainingSession();
  
  // URL 파라미터에서 sessionId, type, date 가져오기
  const sessionIdParam = searchParams.get('sessionId');
  const typeParam = searchParams.get('type') as 'word' | 'sentence' | 'vocal' | null;
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
        
        // 세션 타입 설정 (대문자로 올 수 있으므로 소문자로 변환)
        const sessionTypeLower = (sessionDetailData.type || '').toLowerCase();
        setSessionType(sessionTypeLower as 'word' | 'sentence' | 'vocal');
        
        // 날짜 포맷팅
        const formatted = formatDate(sessionDetailData.training_date);
        setFormattedDate(formatted);
        
        // training_items에서 완료된 아이템만 필터링하여 WordResult로 변환
        const completedItems = sessionDetailData.training_items?.filter(
          (item) => item.is_completed
        ) ?? [];
        
        // item_index 기준으로 오름차순 정렬 (1번부터 위에서 아래로)
        const sortedCompletedItems = [...completedItems].sort((a, b) => 
          (a.item_index || 0) - (b.item_index || 0)
        );
        
        const wordResults: WordResult[] = sortedCompletedItems.map((item) => {
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
        
        // 발성 연습 여부 확인 (type이 'vocal'인 경우)
        const isVoice = (sessionDetailData.type as string) === 'vocal';
        setIsVoiceTraining(isVoice);
        
        if (isVoice) {
          // 발성 연습 메트릭 설정
          // TODO: 백엔드 API에서 세션 레벨의 메트릭을 제공하면 그 값 사용
          setJitter(0.012);
          setShimmer(0.012);
          setNhr(0.012);
          setHnr(0.012);
          setMaxF0(0.012);
          setMinF0(0.012);
          setLhRatioMeanDb(0.012);
          setLhRatioSdDb(0.012);
        } else {
          // 일반 연습 메트릭 설정 (CPP/CSID)
          // TODO: 백엔드 API에서 세션 레벨의 CPP/CSID를 제공하면 그 값 사용
          setCpp(0.012);
          setCsid(0.012);
        }
        
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
    <div className="self-stretch pt-7 pb-10 flex flex-col justify-start items-center bg-white min-h-screen">
      
      {/* 헤더 */}
      <ResultHeader
        type={sessionType}
        date={formattedDate}
        onBack={handleBack}
      />

      {/* 메인 콘텐츠 영역 */}
      <div className="p-4 md:p-8 flex flex-col justify-start items-center gap-8 w-full">
        
        {/* CPP/CSID 메트릭 카드 (기존 AverageScoreCard 구조 유지) */}
        <div className="w-full max-w-[1220px] bg-gradient-to-br from-green-50 via-green-300 to-yellow-100 rounded-2xl outline outline-[3px] outline-offset-[-3px] outline-green-200 inline-flex flex-col md:flex-row justify-start items-start overflow-hidden">
          <div className="flex-1 p-6 flex flex-col md:flex-row justify-start items-center gap-6">
            <img 
              className="w-full md:w-60 h-auto md:self-stretch p-2.5 object-cover rounded-lg" 
              src={도드미치료사} 
              alt="결과 축하 이미지" 
            />
            <div className="flex-1 p-8 bg-white rounded-2xl shadow-lg inline-flex flex-col justify-start items-start gap-3.5 w-full">
              <div className="w-full h-auto inline-flex justify-start items-start gap-6 flex-wrap content-start">
                {isVoiceTraining ? (
                  // 발성 연습: 8개 메트릭 카드
                  <>
                    {/* Jitter 카드 */}
                    <div className="w-52 h-32 p-4 rounded-xl outline outline-1 outline-offset-[-1px] outline-gray-200 inline-flex flex-col justify-start items-start">
                      <div className="w-44 pb-2 inline-flex justify-start items-start">
                        <div className="flex-1 h-7 relative">
                          <div className="w-28 h-6 left-0 top-[2px] absolute inline-flex justify-center items-center gap-2.5">
                            <div className="left-0 top-0 absolute justify-center text-gray-900 text-base font-medium leading-6">Jitter</div>
                          </div>
                        </div>
                      </div>
                      <div className="w-44 h-16 flex flex-col justify-start items-start">
                        <div className="self-stretch h-10 inline-flex justify-start items-center">
                          <div className="justify-center text-gray-900 text-2xl font-bold leading-10">
                            {jitter !== null ? jitter.toFixed(3) : '0.000'}
                          </div>
                          <div className="justify-center text-gray-500 text-sm font-normal leading-6">%</div>
                        </div>
                      </div>
                    </div>

                    {/* Shimmer 카드 */}
                    <div className="w-52 h-32 p-4 rounded-xl outline outline-1 outline-offset-[-1px] outline-gray-200 inline-flex flex-col justify-start items-start">
                      <div className="w-44 pb-2 inline-flex justify-start items-start">
                        <div className="flex-1 h-7 relative">
                          <div className="w-28 h-6 left-0 top-[2px] absolute inline-flex justify-center items-center gap-2.5">
                            <div className="left-0 top-0 absolute justify-center text-gray-900 text-base font-medium leading-6">Shimmer</div>
                          </div>
                        </div>
                      </div>
                      <div className="w-44 h-16 flex flex-col justify-start items-start">
                        <div className="self-stretch h-10 inline-flex justify-start items-center">
                          <div className="justify-center text-gray-900 text-2xl font-bold leading-10">
                            {shimmer !== null ? shimmer.toFixed(3) : '0.000'}
                          </div>
                          <div className="justify-center text-gray-500 text-sm font-normal leading-6">%</div>
                        </div>
                      </div>
                    </div>

                    {/* NHR 카드 */}
                    <div className="w-52 h-32 p-4 rounded-xl outline outline-1 outline-offset-[-1px] outline-gray-200 inline-flex flex-col justify-start items-start">
                      <div className="w-44 pb-2 inline-flex justify-start items-start">
                        <div className="flex-1 h-7 relative">
                          <div className="w-28 h-6 left-0 top-[2px] absolute inline-flex justify-center items-center gap-2.5">
                            <div className="left-0 top-0 absolute justify-center text-gray-900 text-base font-medium leading-6">NHR</div>
                          </div>
                        </div>
                      </div>
                      <div className="w-44 h-16 flex flex-col justify-start items-start">
                        <div className="self-stretch h-10 inline-flex justify-start items-center">
                          <div className="justify-center text-gray-900 text-2xl font-bold leading-10">
                            {nhr !== null ? nhr.toFixed(3) : '0.000'}
                          </div>
                          <div className="justify-center text-gray-500 text-sm font-normal leading-6">%</div>
                        </div>
                      </div>
                    </div>

                    {/* HNR 카드 */}
                    <div className="w-52 h-32 p-4 rounded-xl outline outline-1 outline-offset-[-1px] outline-gray-200 inline-flex flex-col justify-start items-start">
                      <div className="w-44 pb-2 inline-flex justify-start items-start">
                        <div className="flex-1 h-7 relative">
                          <div className="w-28 h-6 left-0 top-[2px] absolute inline-flex justify-center items-center gap-2.5">
                            <div className="left-0 top-0 absolute justify-center text-gray-900 text-base font-medium leading-6">HNR</div>
                          </div>
                        </div>
                      </div>
                      <div className="w-44 h-16 flex flex-col justify-start items-start">
                        <div className="self-stretch h-10 inline-flex justify-start items-center">
                          <div className="justify-center text-gray-900 text-2xl font-bold leading-10">
                            {hnr !== null ? hnr.toFixed(3) : '0.000'}
                          </div>
                          <div className="justify-center text-gray-500 text-sm font-normal leading-6">%</div>
                        </div>
                      </div>
                    </div>

                    {/* max_f0 카드 */}
                    <div className="w-52 h-32 p-4 rounded-xl outline outline-1 outline-offset-[-1px] outline-gray-200 inline-flex flex-col justify-start items-start">
                      <div className="w-44 pb-2 inline-flex justify-start items-start">
                        <div className="flex-1 h-7 relative">
                          <div className="w-28 h-6 left-0 top-[2px] absolute inline-flex justify-center items-center gap-2.5">
                            <div className="left-0 top-0 absolute justify-center text-gray-900 text-base font-medium leading-6">max_f0</div>
                          </div>
                        </div>
                      </div>
                      <div className="w-44 h-16 flex flex-col justify-start items-start">
                        <div className="self-stretch h-10 inline-flex justify-start items-center">
                          <div className="justify-center text-gray-900 text-2xl font-bold leading-10">
                            {maxF0 !== null ? maxF0.toFixed(3) : '0.000'}
                          </div>
                          <div className="justify-center text-gray-500 text-sm font-normal leading-6">%</div>
                        </div>
                      </div>
                    </div>

                    {/* min_f0 카드 */}
                    <div className="w-52 h-32 p-4 rounded-xl outline outline-1 outline-offset-[-1px] outline-gray-200 inline-flex flex-col justify-start items-start">
                      <div className="w-44 pb-2 inline-flex justify-start items-start">
                        <div className="flex-1 h-7 relative">
                          <div className="w-28 h-6 left-0 top-[2px] absolute inline-flex justify-center items-center gap-2.5">
                            <div className="left-0 top-0 absolute justify-center text-gray-900 text-base font-medium leading-6">min_f0</div>
                          </div>
                        </div>
                      </div>
                      <div className="w-44 h-16 flex flex-col justify-start items-start">
                        <div className="self-stretch h-10 inline-flex justify-start items-center">
                          <div className="justify-center text-gray-900 text-2xl font-bold leading-10">
                            {minF0 !== null ? minF0.toFixed(3) : '0.000'}
                          </div>
                          <div className="justify-center text-gray-500 text-sm font-normal leading-6">%</div>
                        </div>
                      </div>
                    </div>

                    {/* LH_ratio_mean_db 카드 */}
                    <div className="w-52 h-32 p-4 rounded-xl outline outline-1 outline-offset-[-1px] outline-gray-200 inline-flex flex-col justify-start items-start">
                      <div className="w-44 pb-2 inline-flex justify-start items-start">
                        <div className="flex-1 h-7 relative">
                          <div className="w-28 h-6 left-0 top-[2px] absolute inline-flex justify-center items-center gap-2.5">
                            <div className="left-0 top-0 absolute justify-center text-gray-900 text-base font-medium leading-6">LH_ratio_mean_db</div>
                          </div>
                        </div>
                      </div>
                      <div className="w-44 h-16 flex flex-col justify-start items-start">
                        <div className="self-stretch h-10 inline-flex justify-start items-center">
                          <div className="justify-center text-gray-900 text-2xl font-bold leading-10">
                            {lhRatioMeanDb !== null ? lhRatioMeanDb.toFixed(3) : '0.000'}
                          </div>
                          <div className="justify-center text-gray-500 text-sm font-normal leading-6">%</div>
                        </div>
                      </div>
                    </div>

                    {/* LH_ratio_sd_db 카드 */}
                    <div className="w-52 h-32 p-4 rounded-xl outline outline-1 outline-offset-[-1px] outline-gray-200 inline-flex flex-col justify-start items-start">
                      <div className="w-44 pb-2 inline-flex justify-start items-start">
                        <div className="flex-1 h-7 relative">
                          <div className="w-28 h-6 left-0 top-[2px] absolute inline-flex justify-center items-center gap-2.5">
                            <div className="left-0 top-0 absolute justify-center text-gray-900 text-base font-medium leading-6">LH_ratio_sd_db</div>
                          </div>
                        </div>
                      </div>
                      <div className="w-44 h-16 flex flex-col justify-start items-start">
                        <div className="self-stretch h-10 inline-flex justify-start items-center">
                          <div className="justify-center text-gray-900 text-2xl font-bold leading-10">
                            {lhRatioSdDb !== null ? lhRatioSdDb.toFixed(3) : '0.000'}
                          </div>
                          <div className="justify-center text-gray-500 text-sm font-normal leading-6">%</div>
                        </div>
                      </div>
                    </div>
                  </>
                ) : (
                  // 일반 연습: CPP/CSID 2개 카드
                  <>
                    {/* CPP 카드 */}
                    <div className="w-52 h-32 p-4 rounded-xl outline outline-1 outline-offset-[-1px] outline-gray-200 inline-flex flex-col justify-start items-start">
                      <div className="w-44 pb-2 inline-flex justify-start items-start">
                        <div className="flex-1 h-7 relative">
                          <div className="w-28 h-6 left-0 top-[2px] absolute inline-flex justify-center items-center gap-2.5">
                            <div className="left-0 top-0 absolute justify-center text-gray-900 text-base font-medium leading-6">CPP</div>
                          </div>
                        </div>
                      </div>
                      <div className="w-44 h-16 flex flex-col justify-start items-start">
                        <div className="self-stretch h-10 inline-flex justify-start items-center">
                          <div className="justify-center text-gray-900 text-2xl font-bold leading-10">
                            {cpp !== null ? cpp.toFixed(3) : '0.000'}
                          </div>
                          <div className="justify-center text-gray-500 text-sm font-normal leading-6">%</div>
                        </div>
                        <div className="self-stretch pt-1 inline-flex justify-start items-start">
                          <div className="w-full h-6 flex justify-start items-center">
                            <div className="justify-center text-gray-500 text-sm font-normal leading-6">정상 범위: 0</div>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* CSID 카드 */}
                    <div className="w-52 h-32 p-4 rounded-xl outline outline-1 outline-offset-[-1px] outline-gray-200 inline-flex flex-col justify-start items-start">
                      <div className="w-44 pb-2 inline-flex justify-start items-start">
                        <div className="flex-1 h-7 relative">
                          <div className="w-28 h-6 left-0 top-[2px] absolute inline-flex justify-center items-center gap-2.5">
                            <div className="left-0 top-0 absolute justify-center text-gray-900 text-base font-medium leading-6">CSID</div>
                          </div>
                        </div>
                      </div>
                      <div className="w-44 h-16 flex flex-col justify-start items-start">
                        <div className="self-stretch h-10 inline-flex justify-start items-center">
                          <div className="justify-center text-gray-900 text-2xl font-bold leading-10">
                            {csid !== null ? csid.toFixed(3) : '0.000'}
                          </div>
                          <div className="justify-center text-gray-500 text-sm font-normal leading-6">%</div>
                        </div>
                        <div className="self-stretch pt-1 inline-flex justify-start items-start">
                          <div className="w-full h-6 flex justify-start items-center">
                            <div className="justify-center text-gray-500 text-sm font-normal leading-6">정상 범위: 0</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </>
                )}
              </div>

              {/* 피드백 메시지 - 숨김 처리 */}
              {/* <div className="self-stretch p-6 bg-green-50 rounded-2xl flex flex-col justify-start items-start">
                <div className="self-stretch inline-flex justify-start items-center gap-2.5">
                  <div className="justify-start text-slate-700 text-2xl font-semibold leading-8">
                    {_overallFeedback}
                  </div>
                </div>
              </div> */}
            </div>
          </div>
        </div>
        
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
