import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { getTrainingSession, type CreateTrainingSessionResponse } from '@/features/training-session/api';
import { getSessionItemByIndex, type SessionItemResponse } from '@/features/training-session/api/session-item-search';
import { createInitialVideoState, type VideoState } from '@/features/practice/types';

interface UsePracticeSessionReturn {
  sessionId: string | null;
  sessionType: 'word' | 'sentence' | 'vocal' | null;
  itemIndex: string | null;
  sessionData: CreateTrainingSessionResponse | null;
  currentItem: SessionItemResponse | null;
  isLoading: boolean;
  error: string | null;
  setCurrentItem: (item: SessionItemResponse | null) => void;
  setSessionData: (data: CreateTrainingSessionResponse | null) => void;
  setVideoState: (state: VideoState) => void;
}

/**
 * 연습 세션 데이터 관리 Hook
 * URL 파라미터에서 세션 정보를 읽어와 초기 데이터 로드
 */
export const usePracticeSession = (
  onVideoStateUpdate: (state: VideoState) => void
): UsePracticeSessionReturn => {
  const [searchParams] = useSearchParams();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentItem, setCurrentItem] = useState<SessionItemResponse | null>(null);
  const [sessionData, setSessionData] = useState<CreateTrainingSessionResponse | null>(null);

  const sessionIdParam = searchParams.get('sessionId');
  const sessionTypeParam = searchParams.get('type') as 'word' | 'sentence' | 'vocal' | null;
  const itemIndexParam = searchParams.get('itemIndex');

  useEffect(() => {
    const loadSessionData = async () => {
      if (!sessionIdParam || !sessionTypeParam) {
        setError('세션 정보가 없습니다. 홈페이지에서 다시 시작해주세요.');
        setIsLoading(false);
        return;
      }

      try {
        const sessionId = Number(sessionIdParam);
        if (isNaN(sessionId)) {
          setError('세션 ID가 유효하지 않습니다.');
          setIsLoading(false);
          return;
        }

        const currentItemIndex = itemIndexParam !== null ? parseInt(itemIndexParam, 10) : 0;
        if (isNaN(currentItemIndex) || currentItemIndex < 0) {
          setError('유효하지 않은 아이템 인덱스입니다.');
          setIsLoading(false);
          return;
        }

        // 세션 정보와 현재 아이템을 병렬로 조회
        const [fetchedSessionData, currentItemData] = await Promise.all([
          getTrainingSession(sessionId),
          getSessionItemByIndex(sessionId, currentItemIndex)
        ]);

        setSessionData(fetchedSessionData);
        setCurrentItem(currentItemData);

        // 비디오 상태 설정
        if (currentItemData.video_url != null) {
          if (currentItemData.composited_video_url != null) {
            onVideoStateUpdate({
              userVideoUrl: currentItemData.video_url,
              compositedVideoUrl: currentItemData.composited_video_url,
              compositedVideoError: null,
              isLoadingComposited: false,
            });
          } else if (currentItemData.is_completed) {
            onVideoStateUpdate({
              userVideoUrl: currentItemData.video_url,
              compositedVideoUrl: undefined,
              compositedVideoError: null,
              isLoadingComposited: true,
            });
          } else {
            onVideoStateUpdate({
              userVideoUrl: currentItemData.video_url,
              compositedVideoUrl: undefined,
              compositedVideoError: null,
              isLoadingComposited: false,
            });
          }
        } else {
          onVideoStateUpdate(createInitialVideoState());
        }

        setIsLoading(false);
      } catch (err) {
        console.error('세션 데이터 로드 실패:', err);
        setError('세션 데이터를 불러오는데 실패했습니다.');
        setIsLoading(false);
      }
    };

    loadSessionData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionIdParam, sessionTypeParam, itemIndexParam]);

  return {
    sessionId: sessionIdParam,
    sessionType: sessionTypeParam,
    itemIndex: itemIndexParam,
    sessionData,
    currentItem,
    isLoading,
    error,
    setCurrentItem,
    setSessionData,
    setVideoState: onVideoStateUpdate,
  };
};

