import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { ResultHeader } from '@/pages/common';
import { ResultVideoDisplay, FeedbackCard } from './components';
import { getSessionItemByIndex, getSessionItemErrorMessage, type SessionItemResponse } from '@/api/trainingSession/session-item-search';
import { useCompositedVideoPolling } from '@/hooks/practice';
import type { PraatMetrics } from '@/api/trainingSession/praat';

const ResultDetailPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [itemData, setItemData] = useState<SessionItemResponse | null>(null);
  const [compositedVideoUrl, setCompositedVideoUrl] = useState<string | undefined>(undefined);
  const [compositedVideoError, setCompositedVideoError] = useState<string | null>(null);
  const [isLoadingCompositedVideo, setIsLoadingCompositedVideo] = useState(false);
  const [praatData, setPraatData] = useState<PraatMetrics | null>(null);


  // URL 파라미터에서 sessionId, type, itemIndex, date 가져오기
  const sessionIdParam = searchParams.get('sessionId');
  const typeParam = searchParams.get('type') as 'word' | 'sentence' | 'vocal' | null;
  const itemIndexParam = searchParams.get('itemIndex');
  const dateParam = searchParams.get('date'); // training-history에서 온 경우 날짜 파라미터

  // 세션 아이템 상세 조회 API 호출
  useEffect(() => {
    const loadItemDetail = async () => {
      if (!sessionIdParam || !typeParam || !itemIndexParam) {
        setError('세션 정보가 없습니다. 결과 목록 페이지에서 다시 시작해주세요.');
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        setError(null);
        
        const sessionId = Number(sessionIdParam);
        const itemIndex = Number(itemIndexParam);
        
        if (isNaN(sessionId) || isNaN(itemIndex)) {
          setError('세션 ID 또는 아이템 인덱스가 유효하지 않습니다.');
          setIsLoading(false);
          return;
        }
        
        // 세션 아이템 상세 조회 API 호출
        const itemDetailData = await getSessionItemByIndex(sessionId, itemIndex);
        
        setItemData(itemDetailData);
        
        // composited_video_url이 있고 null이 아니면 바로 설정
        // 필드가 없거나(null 또는 undefined) null이면 초기화
        if (itemDetailData.composited_video_url != null) {
          setCompositedVideoUrl(itemDetailData.composited_video_url);
          setCompositedVideoError(null);
          setIsLoadingCompositedVideo(false);
        } else {
          // 없거나 null이면 초기화
          setCompositedVideoUrl(undefined);
          setCompositedVideoError(null);
          // is_completed가 true이고 composited_video_url이 없으면 폴링 시작
          if (itemDetailData.is_completed && !itemDetailData.composited_video_url) {
            setIsLoadingCompositedVideo(true);
          }
        }
        
        // Praat 데이터 설정 (아이템 상세 조회 API 응답에 포함된 praat 데이터 사용)
        if (itemDetailData.praat) {
          // praat_id를 id로 매핑하여 PraatMetrics 타입에 맞춤
          setPraatData({ ...itemDetailData.praat, id: itemDetailData.praat.id ?? itemDetailData.praat.praat_id ?? 0 } as PraatMetrics);
        } else {
          setPraatData(null);
        }
        
        setIsLoading(false);
      } catch (err: unknown) {
        console.error('세션 아이템 상세 조회 실패:', err);
        
        const errorMessage = getSessionItemErrorMessage(err);
        setError(errorMessage);
        setIsLoading(false);
      }
    };

    loadItemDetail();
  }, [sessionIdParam, typeParam, itemIndexParam]);

  // 폴링 조건 계산
  const sessionIdNum = sessionIdParam ? Number(sessionIdParam) : undefined;
  const pollingEnabled = Boolean(
    itemData?.is_completed &&
    sessionIdParam &&
    !isNaN(sessionIdNum || NaN) &&
    itemData?.item_id &&
    !compositedVideoUrl && // 이미 받은 로컬 URL 없음
    !itemData?.composited_video_url // 서버에도 없음
  );

  // 공통 폴링 훅 사용
  const { url: polledUrl, loading: polledLoading, error: polledError } = useCompositedVideoPolling(
    sessionIdNum,
    itemData?.item_id,
    {
      enabled: pollingEnabled,
      maxTries: 10,
      baseIntervalMs: 10_000,
      backoff: false, // 기본적으로 고정 간격 사용 (필요시 true로 변경)
    }
  );

  // 폴링 결과를 로컬 상태에 반영
  useEffect(() => {
    if (polledUrl) {
      setCompositedVideoUrl(polledUrl);
      setIsLoadingCompositedVideo(false);
      setCompositedVideoError(null);
      // itemData에도 반영하여 중복 폴링 방지
      setItemData((prev) =>
        prev ? { ...prev, composited_video_url: polledUrl } : prev
      );
    }
  }, [polledUrl]);

  useEffect(() => {
    setIsLoadingCompositedVideo(pollingEnabled && polledLoading);
  }, [pollingEnabled, polledLoading]);

  useEffect(() => {
    if (polledError) {
      setCompositedVideoError(polledError);
    }
  }, [polledError]);

  // 이전 페이지(result-list)로 돌아가기
  const handleBack = () => {
    if (sessionIdParam && typeParam) {
      let listUrl = `/result-list?sessionId=${sessionIdParam}&type=${typeParam}`;
      // date 파라미터가 있으면 함께 전달
      if (dateParam) {
        listUrl += `&date=${dateParam}`;
      }
      navigate(listUrl);
    } else {
      navigate('/result-list');
    }
  };

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
            onClick={handleBack}
            className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            돌아가기
          </button>
        </div>
      </div>
    );
  }

  // 데이터가 없는 경우
  if (!itemData) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-6">
          <div className="text-6xl mb-4">📊</div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">데이터가 없습니다</h2>
          <p className="text-gray-600 mb-6">
            아이템 정보를 찾을 수 없습니다.
          </p>
          <button 
            onClick={handleBack}
            className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            돌아가기
          </button>
        </div>
      </div>
    );
  }

  // 헤더 제목 결정 (word 또는 sentence 중 null이 아닌 것)
  const headerTitle = itemData.word || itemData.sentence || '';

  return (
    <div className="self-stretch pt-7 pb-10 flex flex-col justify-start items-center bg-white min-h-screen">
      {/* 헤더 */}
      <ResultHeader
        type={typeParam || 'word'}
        date="상세 피드백 결과"
        onBack={handleBack}
        title={headerTitle}
      />

      {/* 메인 콘텐츠 영역 */}
      <div className="p-4 md:p-8 flex flex-col justify-start items-center gap-8 w-full max-w-7xl mx-auto">
        {/* 영상 비교 컴포넌트 */}
        <ResultVideoDisplay
          userVideoUrl={itemData.video_url || undefined}
          compositedVideoUrl={compositedVideoUrl}
          isLoadingCompositedVideo={isLoadingCompositedVideo}
          compositedVideoError={compositedVideoError}
        />
        
        {/* 피드백 카드 */}
        <FeedbackCard hideSections={true} praatData={praatData} praatLoading={false} />
      </div>
    </div>
  );
};

export default ResultDetailPage;
