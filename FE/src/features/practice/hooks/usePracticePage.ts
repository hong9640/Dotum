import { useState, useEffect, useCallback } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { getSessionItemByIndex, getSessionItemErrorMessage, type SessionItemResponse } from "@/features/training-session/api/session-item-search";
import { getTrainingSession, type CreateTrainingSessionResponse } from "@/features/training-session/api";
import { submitCurrentItem, type SubmitCurrentItemResponse } from "@/features/practice/api";
import { reuploadVideo, type VideoReuploadResponse } from "@/features/practice/api/video-reupload";
import { createInitialUploadState, type UploadState } from "@/features/practice/types";
import { handleSessionCompletion } from "../utils/sessionCompletion";
import { handleUploadError } from "../utils/uploadErrorHandler";

export interface UsePracticePageReturn {
  // 상태
  isLoading: boolean;
  error: string | null;
  currentItem: SessionItemResponse | null;
  sessionData: CreateTrainingSessionResponse | null;
  uploadState: UploadState;
  isCompletingSession: boolean;
  
  // URL 파라미터
  sessionIdParam: string | null;
  sessionTypeParam: 'word' | 'sentence' | 'vocal' | null;
  
  // 핸들러
  handleSave: (file: File, blobUrl: string) => void;
  handleRetake: () => void;
  handleUpload: () => Promise<void>;
  handleNextWord: () => Promise<void>;
  handlePreviousWord: () => Promise<void>;
  updateUrl: (itemIndex: number) => void;
}

/**
 * PracticePage의 모든 비즈니스 로직을 관리하는 훅
 */
export const usePracticePage = (): UsePracticePageReturn => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  
  // 상태
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentItem, setCurrentItem] = useState<SessionItemResponse | null>(null);
  const [sessionData, setSessionDataState] = useState<CreateTrainingSessionResponse | null>(null);
  const [uploadState, setUploadState] = useState<UploadState>(createInitialUploadState());
  const [isCompletingSession, setIsCompletingSession] = useState(false);

  // URL 파라미터
  const sessionIdParam = searchParams.get('sessionId');
  const sessionTypeParam = searchParams.get('type') as 'word' | 'sentence' | 'vocal' | null;
  const itemIndexParam = searchParams.get('itemIndex');

  // URL 업데이트 헬퍼 함수
  const updateUrl = useCallback((itemIndex: number) => {
    if (!sessionIdParam || !sessionTypeParam) return;
    navigate(`/practice?sessionId=${sessionIdParam}&type=${sessionTypeParam}&itemIndex=${itemIndex}`, { replace: true });
  }, [navigate, sessionIdParam, sessionTypeParam]);

  // 세션 데이터 로드
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
        
        setSessionDataState(fetchedSessionData);
        setCurrentItem(currentItemData);
        
        // URL에 itemIndex가 없거나 다른 경우 URL 업데이트
        if (itemIndexParam === null || parseInt(itemIndexParam, 10) !== currentItemData.item_index) {
          updateUrl(currentItemData.item_index);
        }
        
        setIsLoading(false);
      } catch (err) {
        console.error('세션 데이터 로드 실패:', err);
        const errorMessage = getSessionItemErrorMessage(err);
        setError(errorMessage);
        setIsLoading(false);
      }
    };

    loadSessionData();
  }, [sessionIdParam, sessionTypeParam, itemIndexParam, updateUrl]);

  const handleSave = useCallback((file: File, _blobUrl: string) => {
    setUploadState(prev => ({ ...prev, file }));
  }, []);

  const handleRetake = useCallback(() => {
    setUploadState(createInitialUploadState());
  }, []);

  const handleUpload = useCallback(async () => {
    if (uploadState.isUploading) return;
    
    if (!uploadState.file || !sessionIdParam || !currentItem) {
      setUploadState(prev => ({ ...prev, error: '업로드할 파일이나 세션 정보가 없습니다.' }));
      return;
    }

    const sessionId = Number(sessionIdParam);
    if (isNaN(sessionId)) {
      setUploadState(prev => ({ ...prev, error: '유효하지 않은 세션 ID입니다.' }));
      return;
    }

    try {
      setUploadState(prev => ({ ...prev, isUploading: true, error: null }));
      
      let response: SubmitCurrentItemResponse | VideoReuploadResponse;
      
      if (currentItem.is_completed) {
        response = await reuploadVideo(sessionId, currentItem.item_id, uploadState.file);
      } else {
        response = await submitCurrentItem(sessionId, uploadState.file);
      }
      
      if (response.session) {
        setSessionDataState(response.session);
        
        const updatedItem = response.session.training_items?.find(
          (item) => item.item_id === currentItem.item_id
        );
        
        if (updatedItem) {
          const hasNext = currentItem.has_next;
          
          setCurrentItem({
            ...currentItem,
            is_completed: updatedItem.is_completed,
            video_url: updatedItem.video_url ?? currentItem.video_url,
            composited_video_url: updatedItem.composited_video_url ?? currentItem.composited_video_url,
            media_file_id: updatedItem.media_file_id ?? currentItem.media_file_id,
          });
          
          setUploadState(prev => ({ ...prev, file: null }));
          
          if (hasNext) {
            const nextItemIndex = (currentItem.item_index || 0) + 1;
            
            try {
              const nextItemData = await getSessionItemByIndex(sessionId, nextItemIndex);
              setCurrentItem(nextItemData);
              
              setTimeout(() => {
                updateUrl(nextItemData.item_index);
              }, 50);
            } catch (err) {
              console.error('다음 아이템 로드 실패:', err);
              const errorMessage = getSessionItemErrorMessage(err);
              setError(errorMessage);
            }
          } else {
            // 마지막 아이템이면 세션 완료 처리
            if (!sessionIdParam || !sessionTypeParam) {
              setError('세션 정보가 없습니다. 홈페이지에서 다시 시작해주세요.');
              return;
            }
            
            setIsCompletingSession(true);
            try {
              await handleSessionCompletion({
                sessionId,
                sessionIdParam,
                sessionTypeParam,
                onNavigate: (url) => navigate(url),
              });
            } finally {
              setIsCompletingSession(false);
            }
          }
        } else {
          setCurrentItem({
            ...currentItem,
            is_completed: true,
            video_url: response.video_url || currentItem.video_url,
          });
        }
      } else {
        setCurrentItem({
          ...currentItem,
          is_completed: true,
          video_url: response.video_url || currentItem.video_url,
        });
      }
    } catch (err: unknown) {
      console.error('📥 영상 업로드 실패:', err);
      handleUploadError({
        error: err,
        onNavigate: (url) => navigate(url),
        onRetake: handleRetake,
        onSetError: (errorMsg) => setUploadState(prev => ({ ...prev, error: errorMsg })),
      });
    } finally {
      setUploadState(prev => ({ ...prev, isUploading: false }));
    }
  }, [uploadState, sessionIdParam, currentItem, navigate, updateUrl, sessionTypeParam, handleRetake]);

  const handleNextWord = useCallback(async () => {
    if (!sessionIdParam || !currentItem?.has_next) return;
    
    if ((sessionTypeParam === 'word' || sessionTypeParam === 'sentence') && !currentItem.is_completed) {
      return;
    }
    
    const sessionId = Number(sessionIdParam);
    if (isNaN(sessionId)) return;
    
    try {
      const nextItemIndex = (currentItem.item_index || 0) + 1;
      const nextItemData = await getSessionItemByIndex(sessionId, nextItemIndex);
      
      setCurrentItem(nextItemData);
      setUploadState(prev => ({ ...prev, file: null }));
      
      setTimeout(() => {
        updateUrl(nextItemData.item_index);
      }, 50);
    } catch (err) {
      console.error('다음 아이템 로드 실패:', err);
      const errorMessage = getSessionItemErrorMessage(err);
      setError(errorMessage);
    }
  }, [sessionIdParam, sessionTypeParam, currentItem, updateUrl]);

  const handlePreviousWord = useCallback(async () => {
    if (!sessionIdParam || !currentItem || currentItem.item_index === 0) return;
    
    const sessionId = Number(sessionIdParam);
    if (isNaN(sessionId)) return;
    
    try {
      const prevItemIndex = (currentItem.item_index || 0) - 1;
      const prevItemData = await getSessionItemByIndex(sessionId, prevItemIndex);
      
      setCurrentItem(prevItemData);
      setUploadState(prev => ({ ...prev, file: null }));
      
      setTimeout(() => {
        updateUrl(prevItemData.item_index);
      }, 50);
    } catch (err) {
      console.error('이전 아이템 로드 실패:', err);
      const errorMessage = getSessionItemErrorMessage(err);
      setError(errorMessage);
    }
  }, [sessionIdParam, currentItem, updateUrl]);

  return {
    isLoading,
    error,
    currentItem,
    sessionData,
    uploadState,
    isCompletingSession,
    sessionIdParam,
    sessionTypeParam,
    handleSave,
    handleRetake,
    handleUpload,
    handleNextWord,
    handlePreviousWord,
    updateUrl,
  };
};

