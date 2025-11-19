import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getSessionItemByIndex, getSessionItemErrorMessage, type SessionItemResponse } from '@/features/training-session/api/session-item-search';
import { createInitialVideoState, type VideoState } from '@/features/practice/types';
import type { CreateTrainingSessionResponse } from '@/features/training-session/api';

interface UsePracticeNavigationOptions {
  sessionId: string | null;
  sessionType: string | null;
  currentItem: SessionItemResponse | null;
  sessionData: CreateTrainingSessionResponse | null;
  onItemUpdate: (item: SessionItemResponse) => void;
  onVideoStateUpdate: (state: VideoState) => void;
  onShowResultUpdate: (show: boolean) => void;
  onUploadStateReset: () => void;
  onMediaRecorderRetake: () => void;
}

export const usePracticeNavigation = (options: UsePracticeNavigationOptions) => {
  const {
    sessionId: sessionIdParam,
    sessionType: sessionTypeParam,
    currentItem,
    onItemUpdate,
    onVideoStateUpdate,
    onShowResultUpdate,
    onUploadStateReset,
    onMediaRecorderRetake,
  } = options;

  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);

  const updateUrl = (itemIndex: number) => {
    if (!sessionIdParam || !sessionTypeParam) return;
    navigate(
      `/practice?sessionId=${sessionIdParam}&type=${sessionTypeParam}&itemIndex=${itemIndex}`,
      { replace: true }
    );
  };

  const moveToNext = async () => {
    if (!sessionIdParam || !currentItem?.has_next) return;

    const sessionId = Number(sessionIdParam);
    if (isNaN(sessionId)) return;

    // 단어/문장 연습인 경우, 업로드 완료되지 않았으면 이동 불가
    if ((sessionTypeParam === 'word' || sessionTypeParam === 'sentence') && !currentItem.is_completed) {
      return;
    }

    try {
      onShowResultUpdate(false);
      const nextItemIndex = (currentItem.item_index || 0) + 1;
      const nextItemData = await getSessionItemByIndex(sessionId, nextItemIndex);

      onItemUpdate(nextItemData);
      onShowResultUpdate(false);

      // 비디오 상태 설정
      if (nextItemData.video_url != null) {
        if (nextItemData.composited_video_url != null) {
          onVideoStateUpdate({
            userVideoUrl: nextItemData.video_url,
            compositedVideoUrl: nextItemData.composited_video_url,
            compositedVideoError: null,
            isLoadingComposited: false,
          });
        } else {
          onVideoStateUpdate({
            userVideoUrl: nextItemData.video_url,
            compositedVideoUrl: undefined,
            compositedVideoError: null,
            isLoadingComposited: false,
          });
        }
      } else {
        onVideoStateUpdate(createInitialVideoState());
      }

      onUploadStateReset();
      onMediaRecorderRetake();

      setTimeout(() => {
        updateUrl(nextItemData.item_index);
      }, 50);
    } catch (err) {
      console.error('다음 아이템 로드 실패:', err);
      const errorMessage = getSessionItemErrorMessage(err);
      setError(errorMessage);
    }
  };

  const moveToPrevious = async () => {
    if (!sessionIdParam || !currentItem || currentItem.item_index === 0) return;

    const sessionId = Number(sessionIdParam);
    if (isNaN(sessionId)) return;

    try {
      onShowResultUpdate(false);
      const prevItemIndex = (currentItem.item_index || 0) - 1;
      const prevItemData = await getSessionItemByIndex(sessionId, prevItemIndex);

      onItemUpdate(prevItemData);
      onShowResultUpdate(false);

      // 비디오 상태 설정
      if (prevItemData.video_url != null) {
        if (prevItemData.composited_video_url != null) {
          onVideoStateUpdate({
            userVideoUrl: prevItemData.video_url,
            compositedVideoUrl: prevItemData.composited_video_url,
            compositedVideoError: null,
            isLoadingComposited: false,
          });
        } else {
          onVideoStateUpdate({
            userVideoUrl: prevItemData.video_url,
            compositedVideoUrl: undefined,
            compositedVideoError: null,
            isLoadingComposited: false,
          });
        }
      } else {
        onVideoStateUpdate(createInitialVideoState());
      }

      onUploadStateReset();
      onMediaRecorderRetake();

      setTimeout(() => {
        updateUrl(prevItemData.item_index);
      }, 50);
    } catch (err) {
      console.error('이전 아이템 로드 실패:', err);
      const errorMessage = getSessionItemErrorMessage(err);
      setError(errorMessage);
    }
  };

  return {
    moveToNext,
    moveToPrevious,
    updateUrl,
    navigationError: error,
  };
};

