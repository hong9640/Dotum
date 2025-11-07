import React, { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useMediaRecorder } from "@/hooks/useMediaRecorder";
import { usePracticeStore } from "@/stores/practiceStore";
import TrainingLayout from "@/pages/practice/components/TrainingLayout";
import PracticeComponent from "@/pages/practice/components/practice/PracticeComponent";
import ResultComponent from "@/pages/practice/components/result/ResultComponent";
import { getSessionItemByIndex, getSessionItemErrorMessage, type SessionItemResponse } from "@/api/training-session/sessionItemSearch";
import { getTrainingSession, type CreateTrainingSessionResponse } from "@/api/training-session";
import { submitCurrentItem, type SubmitCurrentItemResponse } from "@/api/practice";
import { reuploadVideo, type VideoReuploadResponse } from "@/api/practice/videoReupload";
import { useCompositedVideoPolling } from "@/hooks/useCompositedVideoPolling";

const PracticePage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentItem, setCurrentItem] = useState<SessionItemResponse | null>(null);
  const [sessionData, setSessionDataState] = useState<CreateTrainingSessionResponse | null>(null);
  const [showResult, setShowResult] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [recordedFile, setRecordedFile] = useState<File | null>(null);
  const [userVideoUrl, setUserVideoUrl] = useState<string | undefined>(undefined);
  const [compositedVideoUrl, setCompositedVideoUrl] = useState<string | undefined>(undefined);
  const [compositedVideoError, setCompositedVideoError] = useState<string | null>(null);
  const [isLoadingCompositedVideo, setIsLoadingCompositedVideo] = useState(false);
  
  // 상태 관리
  const { 
    addRecordedVideo,
    setSessionData
  } = usePracticeStore();

  // URL 파라미터에서 세션 정보 가져오기
  const sessionIdParam = searchParams.get('sessionId');
  const sessionTypeParam = searchParams.get('type') as 'word' | 'sentence' | null;
  const itemIndexParam = searchParams.get('itemIndex');
  
  // URL 업데이트 헬퍼 함수
  const updateUrl = (itemIndex: number) => {
    if (!sessionIdParam || !sessionTypeParam) return;
    navigate(`/practice?sessionId=${sessionIdParam}&type=${sessionTypeParam}&itemIndex=${itemIndex}`, { replace: true });
  };

  // 세션 데이터 로드
  useEffect(() => {
    const loadSessionData = async () => {
      if (!sessionIdParam || !sessionTypeParam) {
        setError('세션 정보가 없습니다. 홈페이지에서 다시 시작해주세요.');
        setIsLoading(false);
        return;
      }

      try {
        console.log('세션 데이터 로드 중...', { sessionId: sessionIdParam, type: sessionTypeParam });
        
        const sessionId = Number(sessionIdParam);
        if (isNaN(sessionId)) {
          setError('세션 ID가 유효하지 않습니다.');
          setIsLoading(false);
          return;
        }
        
        // URL에서 itemIndex 가져오기 (없으면 기본값 0)
        const currentItemIndex = itemIndexParam !== null ? parseInt(itemIndexParam, 10) : 0;
        if (isNaN(currentItemIndex) || currentItemIndex < 0) {
          setError('유효하지 않은 아이템 인덱스입니다.');
          setIsLoading(false);
          return;
        }
        
        // 세션 정보와 현재 아이템을 병렬로 조회
        const [sessionData, currentItemData] = await Promise.all([
          getTrainingSession(sessionId),
          getSessionItemByIndex(sessionId, currentItemIndex)
        ]);
        
        setSessionDataState(sessionData);
        setCurrentItem(currentItemData);
        
        // userVideoUrl 설정 (video_url이 있으면 설정)
        if (currentItemData.video_url != null) {
          setUserVideoUrl(currentItemData.video_url);
        } else {
          setUserVideoUrl(undefined);
        }
        
        // composited_video_url이 있고 null이 아니면 바로 설정
        // 필드가 없거나(null 또는 undefined) null이면 초기화 (폴링으로 가져올 예정)
        if (currentItemData.composited_video_url != null) {
          setCompositedVideoUrl(currentItemData.composited_video_url);
          setCompositedVideoError(null);
          setIsLoadingCompositedVideo(false);
        } else {
          // 없거나 null이면 초기화
          setCompositedVideoUrl(undefined);
          setCompositedVideoError(null);
          
          // is_completed가 true이고 composited_video_url이 없으면 폴링 시작
          if (currentItemData.is_completed && !currentItemData.composited_video_url) {
            console.log('🚀 직접 폴링 시작 (loadSessionData 내부):', {
              item_id: currentItemData.item_id,
              sessionId,
            });
            // 폴링을 즉시 시작하도록 상태 설정
            setIsLoadingCompositedVideo(true);
            // 폴링은 useEffect 내에서 처리 (showResult 설정 후 실행될 것)
          }
        }
        
        // URL에 itemIndex가 없거나 다른 경우 URL 업데이트
        if (itemIndexParam === null || parseInt(itemIndexParam, 10) !== currentItemData.item_index) {
          updateUrl(currentItemData.item_index);
        }
        
        // 현재 아이템의 단어/문장 설정
        const targetText = currentItemData.word || currentItemData.sentence || '';
        
        // 세션 데이터 설정 (실제 API 데이터 반영)
        setSessionData(sessionIdParam, sessionTypeParam, [targetText], sessionData?.total_items || 10, currentItemData.item_index);
        
        // 아이템이 완료된 경우 결과 페이지 표시
        if (currentItemData.is_completed) {
          setShowResult(true);
        } else {
          setShowResult(false);
        }
        
        console.log('📋 합성 영상 데이터 설정 완료:', {
          is_completed: currentItemData.is_completed,
          item_id: currentItemData.item_id,
          composited_video_url: currentItemData.composited_video_url,
          showResultWillBe: currentItemData.is_completed,
        });
        
        setIsLoading(false);
      } catch (err) {
        console.error('세션 데이터 로드 실패:', err);
        const errorMessage = getSessionItemErrorMessage(err);
        setError(errorMessage);
        setIsLoading(false);
      }
    };

    loadSessionData();
  }, [sessionIdParam, sessionTypeParam, itemIndexParam, setSessionData, navigate]);

  // 폴링 조건 계산
  const sessionIdNum = sessionIdParam ? Number(sessionIdParam) : undefined;
  const pollingEnabled = Boolean(
    showResult &&
    currentItem?.is_completed &&
    sessionIdParam &&
    !isNaN(sessionIdNum || NaN) &&
    currentItem?.item_id &&
    !compositedVideoUrl && // 이미 받은 로컬 URL 없음
    !currentItem?.composited_video_url // 서버에도 없음
  );

  // 공통 폴링 훅 사용
  const { url: polledUrl, loading: polledLoading, error: polledError } = useCompositedVideoPolling(
    sessionIdNum,
    currentItem?.item_id,
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
      // currentItem에도 반영하여 중복 폴링 방지
      setCurrentItem((prev) =>
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

  const handleSave = (file: File, blobUrl: string) => {
    console.log("Saved:", file);
    // 녹화된 비디오를 상태에 추가
    addRecordedVideo(blobUrl);
    // 녹화된 파일을 상태에 저장 (업로드용)
    setRecordedFile(file);
  };

  const {
    recordingState,
    permissionError,
    elapsed,
    blobUrl,
    videoRef,
    isCameraReady,
    startRecording,
    stopRecording,
    retake,
  } = useMediaRecorder({ onSave: handleSave });

  const handleViewResults = () => {
    // 녹화 완료 후 결과 페이지 표시 (진행률과 단어는 그대로 유지)
    console.log('🎬 녹화 완료 - 결과 페이지 표시:', {
      currentItemIndex: currentItem?.item_index,
      currentWord: currentItem?.word || currentItem?.sentence,
      progressDisplay: `${(currentItem?.item_index || 0) + 1}/${sessionData?.total_items}`
    });
    
    setShowResult(true);
  };

  const handleRetake = () => {
    // 다시 녹화 버튼 클릭 시 녹화 화면으로 돌아가기
    console.log('🔄 다시 녹화 버튼 클릭');
    
    // 결과 페이지 숨기기
    setShowResult(false);
    
    // 녹화 상태 초기화
    retake(); // useMediaRecorder 상태 초기화 (blobUrl 제거)
    setRecordedFile(null); // 업로드용 파일 초기화
    setUserVideoUrl(undefined); // 사용자 비디오 URL 초기화
    setCompositedVideoUrl(undefined); // Wav2Lip 비디오 URL 초기화
    setCompositedVideoError(null); // Wav2Lip 에러 초기화
    setIsLoadingCompositedVideo(false); // 로딩 상태 초기화
    setUploadError(null); // 업로드 에러 초기화
  };

  const handleUpload = async () => {
    if (!recordedFile || !sessionIdParam || !currentItem) {
      setUploadError('업로드할 파일이나 세션 정보가 없습니다.');
      return;
    }

    const sessionId = Number(sessionIdParam);
    if (isNaN(sessionId)) {
      setUploadError('유효하지 않은 세션 ID입니다.');
      return;
    }

    try {
      setIsUploading(true);
      setUploadError(null);
      
      console.log('📤 영상 업로드 시작:', { 
        sessionId, 
        itemId: currentItem.item_id,
        isCompleted: currentItem.is_completed,
        fileName: recordedFile.name 
      });
      
      let response: SubmitCurrentItemResponse | VideoReuploadResponse;
      
      // is_completed가 true이면 재업로드 API 호출, 아니면 일반 업로드 API 호출
      if (currentItem.is_completed) {
        // 재업로드 API (PUT)
        response = await reuploadVideo(sessionId, currentItem.item_id, recordedFile);
        console.log('📥 영상 재업로드 성공:', response);
      } else {
        // 일반 업로드 API (POST)
        response = await submitCurrentItem(sessionId, recordedFile);
        console.log('📥 영상 업로드 성공:', response);
      }
      
      // 업로드된 사용자 비디오 URL 저장 (있을 경우)
      setUserVideoUrl(response.video_url || undefined);
      
      // 응답에서 업데이트된 세션 데이터 반영
      if (response.session) {
        setSessionDataState(response.session);
        
        // 업로드 성공 후 응답의 training_items에서 현재 아이템 정보를 찾아 업데이트
        const updatedItem = response.session.training_items?.find(
          (item) => item.item_id === currentItem.item_id
        );
        
        if (updatedItem) {
          // 변경되는 필드만 업데이트: is_completed, video_url, composited_video_url, media_file_id
          setCurrentItem({
            ...currentItem,
            is_completed: updatedItem.is_completed,
            video_url: updatedItem.video_url ?? currentItem.video_url,
            composited_video_url: updatedItem.composited_video_url ?? currentItem.composited_video_url,
            media_file_id: updatedItem.media_file_id ?? currentItem.media_file_id,
          });
          
          // composited_video_url이 응답에 있고 null이 아니면 바로 설정
          // 필드가 없거나 null이면 초기화 (폴링으로 가져올 예정)
          if (updatedItem.composited_video_url != null) {
            setCompositedVideoUrl(updatedItem.composited_video_url);
            setCompositedVideoError(null);
            setIsLoadingCompositedVideo(false);
          } else {
            // 없거나 null이면 초기화하여 폴링이 시작되도록 함
            setCompositedVideoUrl(undefined);
            setCompositedVideoError(null);
          }
          
          console.log('📥 업로드 후 아이템 정보 갱신:', {
            is_completed: updatedItem.is_completed,
            video_url: updatedItem.video_url,
            composited_video_url: updatedItem.composited_video_url,
            media_file_id: updatedItem.media_file_id,
          });
          
          // 업로드 성공 시 결과 페이지 표시
          // 업로드 응답에서 is_completed === true && !composited_video_url이면
          // showResult(true)를 먼저 켠 뒤 setIsLoadingCompositedVideo(true)를 함께 세팅
          const needsPolling = updatedItem.is_completed && !updatedItem.composited_video_url;
          
          setShowResult(true);
          
          // 폴링이 필요하면 로딩 상태 설정
          if (needsPolling) {
            setIsLoadingCompositedVideo(true);
          }
        } else {
          // training_items에서 찾지 못한 경우 (없어야 하지만 방어적 코드)
          console.warn('응답의 training_items에서 현재 아이템을 찾지 못했습니다.');
          // 최소한 is_completed는 업데이트
          setCurrentItem({
            ...currentItem,
            is_completed: true,
            video_url: response.video_url || currentItem.video_url,
          });
          
          // 기본적으로 결과 페이지 표시
          setShowResult(true);
        }
      } else {
        // response.session이 없는 경우 (없어야 하지만 방어적 코드)
        console.warn('응답에 session 정보가 없습니다.');
        // 최소한 is_completed는 업데이트
        setCurrentItem({
          ...currentItem,
          is_completed: true,
          video_url: response.video_url || currentItem.video_url,
        });
        
        // 기본적으로 결과 페이지 표시
        setShowResult(true);
      }
      
      // TODO: 백엔드에서 자동 다음 아이템 이동 기능이 결정되면 아래 로직 활성화
      // // 응답에서 다음 아이템이 있으면 현재 아이템 업데이트
      // if (response.next_item) {
      //   setCurrentItem(response.next_item);
      //   
      //   // URL 업데이트
      //   updateUrl(response.next_item.item_index);
      //   
      //   // 다음 아이템의 단어/문장으로 업데이트
      //   const targetText = response.next_item.word || response.next_item.sentence || '';
      //   setSessionData(sessionIdParam, sessionTypeParam!, [targetText], response.session?.total_items || sessionData?.total_items || 10, response.next_item.item_index);
      //   
      //   // 다음 아이템이 완료된 경우 결과 페이지 표시
      //   if (response.next_item.is_completed) {
      //     setShowResult(true);
      //   } else {
      //     setShowResult(false);
      //   }
      // } else {
      //   // 다음 아이템이 없으면 결과 페이지 표시
      //   setShowResult(true);
      // }
      
      // 업로드 완료 후 파일 상태 초기화
      setRecordedFile(null);
      
    } catch (err: any) {
      console.error('📥 영상 업로드 실패:', err);
      
      let errorMessage = '영상 업로드에 실패했습니다.';
      
      if (err.response?.status === 401) {
        errorMessage = '인증이 필요합니다. 다시 로그인해주세요.';
      } else if (err.response?.status === 404) {
        errorMessage = '세션을 찾을 수 없습니다.';
      } else if (err.response?.status === 422) {
        errorMessage = '업로드할 파일이 올바르지 않습니다.';
      } else if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      }
      
      setUploadError(errorMessage);
    } finally {
      setIsUploading(false);
    }
  };

  const handleNextWord = async () => {
    if (!sessionIdParam || !currentItem?.has_next) return;
    
    const sessionId = Number(sessionIdParam);
    if (isNaN(sessionId)) return;
    
    try {
      // 다음 아이템 인덱스 계산
      const nextItemIndex = (currentItem.item_index || 0) + 1;
      
      // 다음 아이템 조회
      const nextItemData = await getSessionItemByIndex(sessionId, nextItemIndex);
      
      console.log('다음 아이템 조회 결과:', nextItemData);
      
      setCurrentItem(nextItemData);
      
      // URL 업데이트
      updateUrl(nextItemData.item_index);
      
      // userVideoUrl 설정 (video_url이 있으면 설정)
      if (nextItemData.video_url != null) {
        setUserVideoUrl(nextItemData.video_url);
      } else {
        setUserVideoUrl(undefined);
      }
      
      // composited_video_url 처리
      // 필드가 있고 null이 아니면 설정, 없거나 null이면 초기화 (폴링으로 가져올 예정)
      if (nextItemData.composited_video_url != null) {
        setCompositedVideoUrl(nextItemData.composited_video_url);
        setCompositedVideoError(null);
        setIsLoadingCompositedVideo(false);
      } else {
        setCompositedVideoUrl(undefined);
        setCompositedVideoError(null);
      }

      // 이전 아이템의 녹화 영상 상태 초기화
      retake(); // useMediaRecorder 상태 초기화 (blobUrl 제거)
      setRecordedFile(null); // 업로드용 파일 초기화
      // setShowResult(false); // 결과 페이지 숨기기
      
      // 다음 아이템이 완료된 경우 결과 페이지 표시
      if (nextItemData.is_completed) {
        setShowResult(true);
      } else {
        setShowResult(false);
      }
      
      // 다음 아이템의 단어/문장으로 업데이트
      const targetText = nextItemData.word || nextItemData.sentence || '';
      setSessionData(sessionIdParam, sessionTypeParam!, [targetText], sessionData?.total_items || 10, nextItemData.item_index);
      
      console.log('다음 아이템으로 이동 완료:', {
        itemIndex: nextItemData.item_index,
        targetText,
        hasNext: nextItemData.has_next,
        showResult
      });
    } catch (err) {
      console.error('다음 아이템 로드 실패:', err);
      const errorMessage = getSessionItemErrorMessage(err);
      setError(errorMessage);
    }
  };

  const handlePreviousWord = async () => {
    if (!sessionIdParam || !currentItem || currentItem.item_index === 0) return;
    
    const sessionId = Number(sessionIdParam);
    if (isNaN(sessionId)) return;
    
    try {
      // 이전 아이템 인덱스 계산
      const prevItemIndex = (currentItem.item_index || 0) - 1;
      
      // 이전 아이템 조회
      const prevItemData = await getSessionItemByIndex(sessionId, prevItemIndex);
      
      console.log('이전 아이템 조회 결과:', prevItemData);
      
      setCurrentItem(prevItemData);
      
      // URL 업데이트
      updateUrl(prevItemData.item_index);
      
      // userVideoUrl 설정 (video_url이 있으면 설정)
      if (prevItemData.video_url != null) {
        setUserVideoUrl(prevItemData.video_url);
      } else {
        setUserVideoUrl(undefined);
      }
      
      // composited_video_url 처리
      // 필드가 있고 null이 아니면 설정, 없거나 null이면 초기화
      if (prevItemData.composited_video_url != null) {
        setCompositedVideoUrl(prevItemData.composited_video_url);
        setCompositedVideoError(null);
        setIsLoadingCompositedVideo(false);
      } else {
        setCompositedVideoUrl(undefined);
        setCompositedVideoError(null);
      }

      // 이전 아이템의 녹화 영상 상태 초기화
      retake(); // useMediaRecorder 상태 초기화 (blobUrl 제거)
      setRecordedFile(null); // 업로드용 파일 초기화
      // setShowResult(false); // 결과 페이지 숨기기
      
      // 이전 아이템이 완료된 경우 결과 페이지 표시
      if (prevItemData.is_completed) {
        setShowResult(true);
      } else {
        setShowResult(false);
      }
      
      // 이전 아이템의 단어/문장으로 업데이트
      const targetText = prevItemData.word || prevItemData.sentence || '';
      setSessionData(sessionIdParam, sessionTypeParam!, [targetText], sessionData?.total_items || 10, prevItemData.item_index);
      
      console.log('이전 아이템으로 이동 완료:', {
        itemIndex: prevItemData.item_index,
        targetText,
        hasNext: prevItemData.has_next,
        showResult
      });
    } catch (err) {
      console.error('이전 아이템 로드 실패:', err);
      const errorMessage = getSessionItemErrorMessage(err);
      setError(errorMessage);
    }
  };

  // 로딩 상태
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-lg text-gray-600">세션 데이터를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  // 에러 상태
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-6">
          <Alert variant="destructive">
            <AlertTitle>오류 발생</AlertTitle>
            <AlertDescription className="mt-2">
              {error}
            </AlertDescription>
          </Alert>
          <button 
            onClick={() => navigate('/')}
            className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            홈으로 돌아가기
          </button>
        </div>
      </div>
    );
  }

  // 데이터가 없는 경우
  if (!currentItem || !sessionData) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-6">
          <Alert>
            <AlertTitle>데이터 없음</AlertTitle>
            <AlertDescription className="mt-2">
              훈련할 데이터가 없습니다.
            </AlertDescription>
          </Alert>
          <button 
            onClick={() => navigate('/')}
            className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            홈으로 돌아가기
          </button>
        </div>
      </div>
    );
  }

  return (
    <TrainingLayout
      currentItem={currentItem}
      sessionData={sessionData}
      onNext={handleNextWord}
      onPrevious={handlePreviousWord}
    >
      {showResult ? (
        <ResultComponent 
          userVideoUrl={userVideoUrl}
          compositedVideoUrl={compositedVideoUrl}
          isLoadingCompositedVideo={isLoadingCompositedVideo}
          compositedVideoError={compositedVideoError}
          onNext={handleNextWord}
          hasNext={currentItem?.has_next ?? false}
          onRetake={handleRetake}
        />
      ) : (
        <PracticeComponent
          recordingState={recordingState}
          elapsed={elapsed}
          blobUrl={blobUrl}
          permissionError={permissionError}
          onStartRecording={startRecording}
          onStopRecording={stopRecording}
          onRetake={retake}
          onViewResults={handleViewResults}
          onUpload={handleUpload}
          isUploading={isUploading}
          uploadError={uploadError}
          isCameraReady={!!isCameraReady}
          videoRef={videoRef}
        />
      )}
    </TrainingLayout>
  );
};

export default PracticePage;