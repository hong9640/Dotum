import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import ResultHeader from './components/ResultHeader';
import WordResultsList from './components/WordResultsList';
import ActionButtons from './components/ActionButtons';
import MetricCard from './components/MetricCard';
import type { WordResult } from './types';
import { getSessionDetail } from '@/api/result-list/sessionDetailSearch';
import { useTrainingSession } from '@/hooks/training-session';
import { retryTrainingSession } from '@/api/training-session/sessionRetry';
import 도드미치료사 from "@/assets/도드미_치료사.png";
import { useAlertDialog } from '@/hooks/useAlertDialog';

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
  const [totalItems, setTotalItems] = useState<number>(0);
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
  const [isRetrying, setIsRetrying] = useState(false);
  
  // 훈련 세션 훅 사용 (새로운 훈련 시작 시 사용)
  const { createWordSession, createSentenceSession, isLoading: isCreatingSession } = useTrainingSession();
  
  // AlertDialog 훅 사용
  const { showAlert, AlertDialog: AlertDialogComponent } = useAlertDialog();
  
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
        
        // 훈련 세션 상세 조회 API 호출
        const sessionDetailData = await getSessionDetail(sessionId);
        
        // 세션 타입 설정 (대문자로 올 수 있으므로 소문자로 변환)
        const sessionTypeLower = (sessionDetailData.type || '').toLowerCase();
        setSessionType(sessionTypeLower as 'word' | 'sentence' | 'vocal');
        
        // total_items 저장 (발성 연습일 때 itemIndex 계산에 필요)
        setTotalItems(sessionDetailData.total_items || 0);
        
        // 날짜 포맷팅
        const formatted = formatDate(sessionDetailData.training_date);
        setFormattedDate(formatted);
        
        // 발성 연습 여부 확인 (type이 'vocal'인 경우)
        // sessionTypeLower 또는 typeParam을 확인하여 발성 연습 여부 판단
        const isVoice = sessionTypeLower === 'vocal' || (typeParam && typeParam.toLowerCase() === 'vocal');
        setIsVoiceTraining(isVoice);
        
        let wordResults: WordResult[];
        
        if (isVoice) {
          // 발성 연습일 때: 5개의 훈련명을 고정으로 표시
          const vocalTrainingNames = [
            '최대 발성 지속 시간 훈련 (MPT)',
            '크레셴도 훈련 (점강)',
            '데크레셴도 훈련 (점약)',
            '순간 강약 전환 훈련',
            '연속 강약 조절 훈련'
          ];
          
          wordResults = vocalTrainingNames.map((trainingName, index) => ({
            id: index + 1,
            word: trainingName,
            feedback: '피드백 정보가 없습니다.',
            score: 0,
          }));
        } else {
          // 일반 연습(단어/문장): 실제 training_items에서 완료된 아이템만 필터링하여 WordResult로 변환
          const completedItems = sessionDetailData.training_items?.filter(
            (item) => item.is_completed
          ) ?? [];
          
          // item_index 기준으로 오름차순 정렬 (1번부터 위에서 아래로)
          const sortedCompletedItems = [...completedItems].sort((a, b) => 
            (a.item_index || 0) - (b.item_index || 0)
          );
          
          wordResults = sortedCompletedItems.map((item) => {
            // word 또는 sentence 필드에서 텍스트 가져오기
            const text = item.word || item.sentence || '';
            
            return {
              id: item.item_index + 1, // 1부터 시작하는 ID
              word: text,
              feedback: item.feedback || '피드백 정보가 없습니다.',
              score: item.score ?? 0, // score가 null이면 0으로 설정
            };
          });
        }
        
        setResultsData(wordResults);
        
        // session_praat_result에서 메트릭 값 가져오기
        const praatResult = sessionDetailData.session_praat_result;
        
        if (isVoice) {
          // 발성 연습 메트릭 설정
          if (praatResult) {
            setJitter(praatResult?.avg_jitter_local ?? null);
            setShimmer(praatResult?.avg_shimmer_local ?? null);
            setNhr(praatResult?.avg_nhr ?? null);
            setHnr(praatResult?.avg_hnr ?? null);
            setMaxF0(praatResult?.avg_max_f0 ?? null);
            setMinF0(praatResult?.avg_min_f0 ?? null);
            setLhRatioMeanDb(praatResult?.avg_lh_ratio_mean_db ?? null);
            setLhRatioSdDb(praatResult?.avg_lh_ratio_sd_db ?? null);
          } else {
            // session_praat_result가 없으면 null로 설정
            setJitter(null);
            setShimmer(null);
            setNhr(null);
            setHnr(null);
            setMaxF0(null);
            setMinF0(null);
            setLhRatioMeanDb(null);
            setLhRatioSdDb(null);
          }
        } else {
          // 일반 연습 메트릭 설정 (CPP/CSID)
          // 백엔드 API에서 세션 레벨의 CPP/CSID를 서버로부터 받아서 사용
          if (praatResult) {
            setCpp(praatResult?.avg_cpp ?? null);
            setCsid(praatResult?.avg_csid ?? null);
          } else {
            setCpp(null);
            setCsid(null);
          }
        }
        
        // 전체 피드백 설정 (백엔드에서 제공하는 overall_feedback 사용, null이면 기본 메시지)
        setOverallFeedback(sessionDetailData.overall_feedback || '피드백 정보가 없습니다.');
        
        setIsLoading(false);
      } catch (err: unknown) {
        console.error('세션 상세 조회 실패:', err);
        
        const enhancedError = err as { status?: number };
        let errorMessage = '세션 상세 조회에 실패했습니다.';
        if (enhancedError.status === 401) {
          errorMessage = '인증이 필요합니다. 다시 로그인해주세요.';
        } else if (enhancedError.status === 404) {
          errorMessage = '세션을 찾을 수 없습니다.';
        }
        
        const errorWithMessage = err as { message?: string };
        if (errorWithMessage.message) {
          errorMessage = errorWithMessage.message;
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
    if (!sessionIdParam || !typeParam) {
      console.error('세션 정보가 없습니다.');
      showAlert({ description: '세션 정보를 찾을 수 없습니다.' });
      return;
    }

    // 발성 연습일 때는 praat-detail로 이동
    if (sessionType === 'vocal' || (typeParam && typeParam.toLowerCase() === 'vocal')) {
      // 발성 연습: 각 훈련의 첫 번째 시도로 이동
      // n = total_items / 5 (각 훈련 반복 횟수)
      // 훈련 인덱스 = result.id - 1 (0, 1, 2, 3, 4)
      // 첫 번째 시도의 itemIndex = 훈련 인덱스 * n
      const n = totalItems > 0 ? Math.floor(totalItems / 5) : 0;
      const trainingIndex = result.id - 1; // 0, 1, 2, 3, 4
      const itemIndex = trainingIndex * n;
      
      let praatUrl = `/praat-detail?sessionId=${sessionIdParam}&itemIndex=${itemIndex}`;
      // date 파라미터가 있으면 함께 전달
      if (dateParam) {
        praatUrl += `&date=${dateParam}`;
      }
      navigate(praatUrl);
    } else {
      // 단어/문장 연습: result-detail 페이지로 이동
      // result.id는 1부터 시작, itemIndex는 0부터 시작하므로 -1 필요
      let detailUrl = `/result-detail?sessionId=${sessionIdParam}&type=${typeParam}&itemIndex=${result.id - 1}`;
      // date 파라미터가 있으면 함께 전달
      if (dateParam) {
        detailUrl += `&date=${dateParam}`;
      }
      navigate(detailUrl);
    }
  };

  const handleRetry = async () => {
    // 이미 재훈련 중이면 중복 실행 방지
    if (isRetrying) return;
    
    if (!sessionIdParam) {
      console.error('세션 ID가 없습니다.');
      showAlert({ description: '세션 정보를 찾을 수 없습니다.' });
      return;
    }

    try {
      setIsRetrying(true);
      
      const sessionId = Number(sessionIdParam);
      if (isNaN(sessionId)) {
        showAlert({ description: '유효하지 않은 세션 ID입니다.' });
        setIsRetrying(false);
        return;
      }

      // 재훈련 API 호출
      const retrySession = await retryTrainingSession(sessionId);
      
      // 성공 시 practice 페이지로 이동 (sessionId, type, itemIndex=0)
      if (retrySession.session_id && retrySession.type) {
        navigate(`/practice?sessionId=${retrySession.session_id}&type=${retrySession.type}&itemIndex=0`);
      } else {
        showAlert({ description: '재훈련 세션 정보가 올바르지 않습니다.' });
        setIsRetrying(false);
      }
    } catch (error: unknown) {
      console.error('재훈련 세션 생성 실패:', error);
      const errorWithMessage = error as { message?: string };
      showAlert({ description: errorWithMessage.message || '재훈련 세션 생성에 실패했습니다.' });
      setIsRetrying(false);
    }
  };

  const handleNewTraining = async () => {
    // 현재 세션의 훈련 타입에 따라 단어 또는 문장 세션 생성
    try {
      if (sessionType === 'word') {
        // 단어 연습 시작과 동일하게 동작
        await createWordSession(10);
      } else {
        // 문장 연습 시작과 동일하게 동작
        await createSentenceSession(10);
      }
    } catch (error) {
      // 에러는 훅에서 처리됨 (toast 메시지 표시)
      console.error('새로운 훈련 세션 생성 실패:', error);
    }
  };

  return (
    <div className="self-stretch pt-7 pb-10 flex flex-col justify-start items-center bg-white min-h-screen">
      {/* AlertDialog */}
      <AlertDialogComponent />
      
      {/* 헤더 */}
      <ResultHeader
        type={sessionType}
        date={formattedDate}
        onBack={handleBack}
      />

      {/* 메인 콘텐츠 영역 */}
      <div className="p-4 md:p-8 flex flex-col justify-start items-center gap-8 w-full">
        
        {/* CPP/CSID 메트릭 카드 (기존 AverageScoreCard 구조 유지) */}
        <div className="w-full max-w-[1220px] bg-gradient-to-br from-green-50 via-green-300 to-yellow-100 rounded-2xl outline outline-[3px] outline-offset-[-3px] outline-green-200 inline-flex flex-col md:flex-row justify-start items-stretch overflow-hidden">
          <div className="p-6 flex flex-col md:flex-row justify-start items-center gap-6 w-full min-w-0">
            
            {/* 이미지 래퍼: 비율로 자리 확보 + 최대 폭 캡 */}
            <div className="w-full md:flex-[0_0_28%] lg:flex-[0_0_32%] xl:flex-[0_0_34%] md:max-w-[340px] lg:max-w-[380px] xl:max-w-[420px] flex justify-center md:justify-start">
              <img 
                src={도드미치료사} 
                alt="결과 축하 이미지"
                className="w-full h-auto p-2.5 object-contain rounded-lg max-w-[340px] md:max-w-[380px] lg:max-w-[420px] max-h-[45vh] min-w-[358px] flex-shrink-0" 
              />
            </div>

            {/* 메트릭 카드: 가변 영역 */}
            <div className="p-8 bg-white rounded-2xl shadow-lg inline-flex flex-col justify-start items-start gap-3.5 flex-1 min-w-0">
              <div className="w-full inline-flex justify-start items-start gap-6 flex-wrap content-start">
                {isVoiceTraining ? (
                  // 발성 연습: 8개 메트릭 카드
                  <>
                    <MetricCard title="Jitter" value={jitter} unit="%"/>
                    <MetricCard title="Shimmer" value={shimmer} unit="%"/>
                    <MetricCard title="NHR" value={nhr} unit="dB"/>
                    <MetricCard title="HNR" value={hnr} unit="dB"/>
                    <MetricCard title="max_f0" value={maxF0} unit="Hz"/>
                    <MetricCard title="min_f0" value={minF0} unit="Hz"/>
                    <MetricCard title="LH_ratio_mean_db" value={lhRatioMeanDb} unit="dB"/>
                    <MetricCard title="LH_ratio_sd_db" value={lhRatioSdDb} unit="dB"/>
                  </>
                ) : (
                  // 일반 연습: CPP/CSID 2개 카드
                  <>
                    <MetricCard title="CPP" value={cpp} normalRange="0" />
                    <MetricCard title="CSID" value={csid} normalRange="0" />
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
          sessionType={sessionType}
        />
        
        {/* 다음 행동 버튼 - 발성 연습이 아닐 때만 표시 */}
        {!isVoiceTraining && (
          <ActionButtons
            onRetry={handleRetry}
            onNewTraining={handleNewTraining}
            isRetrying={isRetrying}
            isLoading={isCreatingSession}
          />
        )}
      </div>
    </div>
  );
};

export default WordSetResults;
