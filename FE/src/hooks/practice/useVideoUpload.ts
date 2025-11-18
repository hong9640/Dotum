import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { submitCurrentItem, type SubmitCurrentItemResponse } from '@/api/practice';
import { reuploadVideo, type VideoReuploadResponse } from '@/api/practice/video-reupload';
import { getSessionItemByIndex, getSessionItemErrorMessage, type SessionItemResponse } from '@/api/trainingSession/session-item-search';
import { getTrainingSession, completeTrainingSession, type CreateTrainingSessionResponse } from '@/api/trainingSession';
import { createInitialVideoState, type VideoState } from '@/types/practice';

interface UseVideoUploadOptions {
  currentItem: SessionItemResponse | null;
  sessionId: number;
  sessionIdParam: string;
  sessionTypeParam: string;
  onItemUpdate: (item: SessionItemResponse) => void;
  onSessionUpdate: (session: CreateTrainingSessionResponse) => void;
  onVideoStateUpdate: (state: VideoState) => void;
  onShowResultUpdate: (show: boolean) => void;
  onUploadStateReset: () => void;
  onMediaRecorderRetake: () => void;
  updateUrl: (itemIndex: number) => void;
  setError: (error: string) => void;
}

export const useVideoUpload = (options: UseVideoUploadOptions) => {
  const {
    currentItem,
    sessionId,
    sessionIdParam,
    sessionTypeParam,
    onItemUpdate,
    onSessionUpdate,
    onVideoStateUpdate,
    onShowResultUpdate,
    onUploadStateReset,
    onMediaRecorderRetake,
    updateUrl,
    setError,
  } = options;

  const navigate = useNavigate();
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const upload = async (file: File) => {
    if (!file || !currentItem) {
      setUploadError('업로드할 파일이나 세션 정보가 없습니다.');
      return null;
    }

    try {
      setIsUploading(true);
      setUploadError(null);

      let response: SubmitCurrentItemResponse | VideoReuploadResponse;

      // is_completed가 true이면 재업로드, 아니면 일반 업로드
      if (currentItem.is_completed) {
        response = await reuploadVideo(sessionId, currentItem.item_id, file);
      } else {
        response = await submitCurrentItem(sessionId, file);
      }

      // 업로드된 사용자 비디오 URL 저장
      onVideoStateUpdate({
        ...createInitialVideoState(),
        userVideoUrl: response.video_url || undefined,
      });

      // 응답에서 업데이트된 세션 데이터 반영
      if (response.session) {
        onSessionUpdate(response.session);

        const updatedItem = response.session.training_items?.find(
          (item: { item_id: number }) => item.item_id === currentItem.item_id
        );

        if (updatedItem) {
          const hasNext = currentItem.has_next;

          // 현재 아이템 업데이트
          onItemUpdate({
            ...currentItem,
            is_completed: updatedItem.is_completed,
            video_url: updatedItem.video_url ?? currentItem.video_url,
            composited_video_url: updatedItem.composited_video_url ?? currentItem.composited_video_url,
            media_file_id: updatedItem.media_file_id ?? currentItem.media_file_id,
          });

          // composited_video_url 상태 업데이트
          if (updatedItem.composited_video_url != null) {
            onVideoStateUpdate({
              userVideoUrl: response.video_url || undefined,
              compositedVideoUrl: updatedItem.composited_video_url,
              compositedVideoError: null,
              isLoadingComposited: false,
            });
          }

          onShowResultUpdate(false);
          onUploadStateReset();
          onMediaRecorderRetake();

          // 다음 아이템으로 이동
          if (hasNext) {
            const nextItemIndex = (currentItem.item_index || 0) + 1;

            try {
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

              setTimeout(() => {
                updateUrl(nextItemData.item_index);
              }, 50);
            } catch (err) {
              console.error('다음 아이템 로드 실패:', err);
              const errorMessage = getSessionItemErrorMessage(err);
              setError(errorMessage);
            }
          } else {
            // 마지막 아이템 - 세션 완료 처리
            if (!sessionIdParam || !sessionTypeParam) {
              console.error('세션 정보가 없어 결과 목록 페이지로 이동할 수 없습니다.');
              setError('세션 정보가 없습니다. 홈페이지에서 다시 시작해주세요.');
              return;
            }

            try {
              const sessionData = await getTrainingSession(sessionId);

              if (sessionData.total_items !== sessionData.completed_items) {
                const trainingType = sessionData.type === 'word' ? '단어' : sessionData.type === 'sentence' ? '문장' : '발성';
                toast.error(`아직 제출하지 않은 ${trainingType} 연습이 있습니다.`);
                return;
              }

              await completeTrainingSession(sessionId);

              const resultListUrl = `/result-list?sessionId=${sessionIdParam}&type=${sessionTypeParam}`;
              navigate(resultListUrl);
            } catch (error: unknown) {
              console.error('세션 완료 처리 실패:', error);
              const errorWithMessage = error as { message?: string };
              setError(errorWithMessage.message || '세션 완료 처리에 실패했습니다.');
            }
          }
        } else {
          // training_items에서 찾지 못한 경우
          onItemUpdate({
            ...currentItem,
            is_completed: true,
            video_url: response.video_url || currentItem.video_url,
          });
          onShowResultUpdate(false);
        }
      } else {
        // 업로드 후 세션 데이터가 응답에 없는 경우 (현재 아이템만 완료 처리)
        onItemUpdate({
          ...currentItem,
          is_completed: true,
          video_url: response.video_url || currentItem.video_url,
        });
        onShowResultUpdate(false);
      }

      toast.success('업로드가 완료되었습니다!');
      return response;
    } catch (err: unknown) {
      console.error('업로드 실패:', err);

      const axiosError = err as { response?: { status?: number } };
      const status = axiosError.response?.status;

      // 에러 코드별 처리
      if (status === 401) {
        toast.error('세션이 만료되었습니다. 다시 로그인해주세요.');
        setIsUploading(false);
        setTimeout(() => navigate('/login'), 1500);
        return null;
      }

      if (status === 404) {
        toast.error('세션을 찾을 수 없습니다. 홈에서 다시 시작해주세요.');
        setIsUploading(false);
        setTimeout(() => navigate('/'), 1500);
        return null;
      }

      if (status === 422) {
        toast.error('파일이 올바르지 않습니다. 다시 녹화해주세요.');
        setIsUploading(false);
        onMediaRecorderRetake();
        return null;
      }

      // 그 외 에러
      let errorMessage = '영상 업로드에 실패했습니다.';
      const axiosErrorWithDetail = err as { response?: { data?: { detail?: string } } };
      if (axiosErrorWithDetail.response?.data?.detail) {
        errorMessage = axiosErrorWithDetail.response.data.detail;
      }

      setUploadError(errorMessage);
      toast.error('업로드에 실패했습니다. 다시 시도해주세요.');
      return null;
    } finally {
      setIsUploading(false);
    }
  };

  return {
    upload,
    isUploading,
    uploadError,
  };
};

