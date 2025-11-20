import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { ResultHeader } from '@/shared/components/result';
import WordResultsList from '../components/WordResultsList';
import ActionButtons from '../components/ActionButtons';
import MetricCard from '../components/MetricCard';
import { useResultList } from '../hooks/useResultList';
import 도드미치료사 from "@/assets/도드미_치료사.png";

const WordSetResults: React.FC = () => {
  const navigate = useNavigate();
  
  // 모든 비즈니스 로직을 훅으로 분리
  const {
    isLoading,
    error,
    resultsData,
    sessionType,
    formattedDate,
    voiceMetrics,
    isVoiceTraining,
    overallFeedback,
    isRetrying,
    isCreatingSession,
    handleBack,
    handleDetailClick,
    handleRetry,
    handleNewTraining,
    AlertDialog: AlertDialogComponent,
  } = useResultList();

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
            아직 완료된 연습 결과가 없습니다.<br />
            연습을 완료한 후 다시 확인해주세요.
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
              <div className="w-full grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {isVoiceTraining ? (
                  // 발성 연습: 8개 메트릭 카드
                  <>
                    <MetricCard title="Jitter" value={voiceMetrics.jitter} unit="%"/>
                    <MetricCard title="Shimmer" value={voiceMetrics.shimmer} unit="%"/>
                    <MetricCard title="NHR" value={voiceMetrics.nhr} unit="dB"/>
                    <MetricCard title="HNR" value={voiceMetrics.hnr} unit="dB"/>
                    <MetricCard title="max_f0" value={voiceMetrics.maxF0} unit="Hz"/>
                    <MetricCard title="min_f0" value={voiceMetrics.minF0} unit="Hz"/>
                    <MetricCard title="LH_ratio_mean_db" value={voiceMetrics.lhRatioMeanDb} unit="dB"/>
                    <MetricCard title="LH_ratio_sd_db" value={voiceMetrics.lhRatioSdDb} unit="dB"/>
                  </>
                ) : (
                  // 일반 연습: CPP/CSID 2개 카드
                  <>
                    <MetricCard title="CPP" value={voiceMetrics.cpp} />
                    <MetricCard title="CSID" value={voiceMetrics.csid} />
                  </>
                )}
              </div>

              {/* 전체 피드백 메시지 */}
              <div className="self-stretch p-6 bg-green-50 rounded-2xl flex flex-col justify-start items-start mt-4">
                <div className="self-stretch inline-flex justify-start items-center gap-2.5">
                  {overallFeedback ? (
                    <div className="justify-start text-slate-700 text-2xl font-semibold leading-8">
                      {overallFeedback}
                    </div>
                  ) : (
                    <div className="flex justify-center items-center w-full py-4">
                      <Loader2 className="w-8 h-8 text-blue-500 animate-spin" strokeWidth={2} />
                    </div>
                  )}
                </div>
              </div>
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
