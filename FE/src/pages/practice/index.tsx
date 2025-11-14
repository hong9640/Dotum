import React, { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useMediaRecorder, useCompositedVideoPolling } from "@/hooks/practice";
import TrainingLayout from "@/pages/practice/components/TrainingLayout";
import PracticeComponent from "@/pages/practice/components/practice/PracticeComponent";
import ResultComponent from "@/pages/practice/components/result/ResultComponent";
import { getSessionItemByIndex, getSessionItemErrorMessage, type SessionItemResponse } from "@/api/trainingSession/sessionItemSearch";
import { getTrainingSession, completeTrainingSession, type CreateTrainingSessionResponse } from "@/api/trainingSession";
import { submitCurrentItem, type SubmitCurrentItemResponse } from "@/api/practice";
import { reuploadVideo, type VideoReuploadResponse } from "@/api/practice/videoReupload";
import { toast } from "sonner";
import { createInitialUploadState, type UploadState, createInitialVideoState, type VideoState } from "@/types/practice";

const PracticePage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentItem, setCurrentItem] = useState<SessionItemResponse | null>(null);
  const [sessionData, setSessionDataState] = useState<CreateTrainingSessionResponse | null>(null);
  const [showResult, setShowResult] = useState(false);
  const [uploadState, setUploadState] = useState<UploadState>(createInitialUploadState());
  const [videoState, setVideoState] = useState<VideoState>(createInitialVideoState());
  

  // URL 파라미터에서 세션 정보 가져오기
  const sessionIdParam = searchParams.get('sessionId');
  const sessionTypeParam = searchParams.get('type') as 'word' | 'sentence' | 'vocal' | null;
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
        const [fetchedSessionData, currentItemData] = await Promise.all([
          getTrainingSession(sessionId),
          getSessionItemByIndex(sessionId, currentItemIndex)
        ]);
        
        setSessionDataState(fetchedSessionData);
        setCurrentItem(currentItemData);
        if (currentItemData.video_url != null) {
          if (currentItemData.composited_video_url != null) {
            // 합성 비디오가 이미 있는 경우
            setVideoState({
              userVideoUrl: currentItemData.video_url,
              compositedVideoUrl: currentItemData.composited_video_url,
              compositedVideoError: null,
              isLoadingComposited: false,
            });
          } else if (currentItemData.is_completed) {
            // 업로드는 완료됐지만 합성이 안된 경우 (폴링 시작)
            setVideoState({
              userVideoUrl: currentItemData.video_url,
              compositedVideoUrl: undefined,
              compositedVideoError: null,
              isLoadingComposited: true,
            });
          } else {
            // 업로드는 있지만 완료되지 않은 경우
            setVideoState({
              userVideoUrl: currentItemData.video_url,
              compositedVideoUrl: undefined,
              compositedVideoError: null,
              isLoadingComposited: false,
            });
          }
        } else {
          // 비디오가 아직 없는 경우
          setVideoState(createInitialVideoState());
        }
        
        // URL에 itemIndex가 없거나 다른 경우 URL 업데이트
        if (itemIndexParam === null || parseInt(itemIndexParam, 10) !== currentItemData.item_index) {
          updateUrl(currentItemData.item_index);
        }
        
        
        // 아이템이 완료된 경우 결과 페이지 표시
        if (currentItemData.is_completed) {
          setShowResult(false);
        } else {
          setShowResult(false);
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionIdParam, sessionTypeParam, itemIndexParam]);

  // 폴링 조건 계산
  const sessionIdNum = sessionIdParam ? Number(sessionIdParam) : undefined;
  const pollingEnabled = Boolean(
    showResult &&
    currentItem?.is_completed &&
    sessionIdParam &&
    !isNaN(sessionIdNum || NaN) &&
    currentItem?.item_id &&
    !videoState.compositedVideoUrl && // 이미 받은 로컬 URL 없음
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
      setVideoState(prev => ({
        ...prev,
        compositedVideoUrl: polledUrl,
        isLoadingComposited: false,
        compositedVideoError: null,
      }));
      // currentItem에도 반영하여 중복 폴링 방지
      setCurrentItem((prev) =>
        prev ? { ...prev, composited_video_url: polledUrl } : prev
      );
    }
  }, [polledUrl]);

  useEffect(() => {
    setVideoState(prev => ({ ...prev, isLoadingComposited: pollingEnabled && polledLoading }));
  }, [pollingEnabled, polledLoading]);

  useEffect(() => {
    if (polledError) {
      setVideoState(prev => ({ ...prev, compositedVideoError: polledError }));
    }
  }, [polledError]);

  const handleSave = (file: File, _blobUrl: string) => {
    // 녹화된 파일을 상태에 저장 (업로드용)
    setUploadState(prev => ({ ...prev, file }));
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
    setShowResult(false);
  };

  const handleRetake = () => {
    // 다시 녹화 버튼 클릭 시 녹화 화면으로 돌아가기
    
    // 결과 페이지 숨기기
    setShowResult(false);
    
    // 녹화 상태 초기화
    retake(); // useMediaRecorder 상태 초기화 (blobUrl 제거)
    setUploadState(createInitialUploadState()); // 업로드 상태 초기화
    setVideoState(createInitialVideoState()); // 비디오 상태 초기화
  };

  const handleUpload = async () => {
    // 이미 업로드 중이면 중복 실행 방지
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
      
      // is_completed가 true이면 재업로드 API 호출, 아니면 일반 업로드 API 호출
      if (currentItem.is_completed) {
        // 재업로드 API (PUT)
        response = await reuploadVideo(sessionId, currentItem.item_id, uploadState.file);
      } else {
        // 일반 업로드 API (POST)
        response = await submitCurrentItem(sessionId, uploadState.file);
      }
      
      // 업로드된 사용자 비디오 URL 저장 (있을 경우)
      setVideoState(prev => ({ ...prev, userVideoUrl: response.video_url || undefined }));
      
      // 응답에서 업데이트된 세션 데이터 반영
      if (response.session) {
        setSessionDataState(response.session);
        
        // 업로드 성공 후 응답의 training_items에서 현재 아이템 정보를 찾아 업데이트
        const updatedItem = response.session.training_items?.find(
          (item) => item.item_id === currentItem.item_id
        );
        
        if (updatedItem) {
          // 업데이트 전에 has_next를 미리 저장 (업데이트 후에는 사용할 수 없음)
          const hasNext = currentItem.has_next;
          
          // 변경되는 필드만 업데이트: is_completed, video_url, composited_video_url, media_file_id
          setCurrentItem({
            ...currentItem,
            is_completed: updatedItem.is_completed,
            video_url: updatedItem.video_url ?? currentItem.video_url,
            composited_video_url: updatedItem.composited_video_url ?? currentItem.composited_video_url,
            media_file_id: updatedItem.media_file_id ?? currentItem.media_file_id,
          });
          
          // composited_video_url 상태 업데이트
          if (updatedItem.composited_video_url != null) {
            setVideoState(prev => ({
              ...prev,
              compositedVideoUrl: updatedItem.composited_video_url!,
              compositedVideoError: null,
              isLoadingComposited: false,
            }));
          } else {
            // 없거나 null이면 폴링 대기 상태로
            setVideoState(prev => ({
              ...prev,
              compositedVideoUrl: undefined,
              compositedVideoError: null,
            }));
          }
          
          // 업로드 성공 시 결과 페이지 표시하지 않음
          setShowResult(false);
          
          // 업로드 완료 후 파일 상태 초기화 (아이템 이동 전에 초기화)
          setUploadState(prev => ({ ...prev, file: null }));
          retake(); // useMediaRecorder 상태 초기화
          
          // 다음 아이템이 있으면 다음 아이템으로 이동
          if (hasNext) {
            // 다음 아이템 인덱스 계산
            const nextItemIndex = (currentItem.item_index || 0) + 1;
            
            try {
              // 다음 아이템 조회
              const nextItemData = await getSessionItemByIndex(sessionId, nextItemIndex);
              
              // 모든 상태를 한 번에 배치 업데이트 (React 18의 자동 배칭 활용)
              setCurrentItem(nextItemData);
              setShowResult(false);
              
              // 비디오 상태 설정
              if (nextItemData.video_url != null) {
                if (nextItemData.composited_video_url != null) {
                  setVideoState({
                    userVideoUrl: nextItemData.video_url,
                    compositedVideoUrl: nextItemData.composited_video_url,
                    compositedVideoError: null,
                    isLoadingComposited: false,
                  });
                } else {
                  setVideoState({
                    userVideoUrl: nextItemData.video_url,
                    compositedVideoUrl: undefined,
                    compositedVideoError: null,
                    isLoadingComposited: false,
                  });
                }
              } else {
                setVideoState(createInitialVideoState());
              }
              
              // 세션 데이터는 이미 currentItem에 저장됨
              
              // URL 업데이트는 약간의 지연을 두어 상태 업데이트가 완료된 후 실행
              setTimeout(() => {
                updateUrl(nextItemData.item_index);
              }, 50);
            } catch (err) {
              console.error('다음 아이템 로드 실패:', err);
              const errorMessage = getSessionItemErrorMessage(err);
              setError(errorMessage);
            }
          } else {
            // 마지막 아이템이면 세션 완료 확인 후 결과 목록 페이지로 이동
            
            if (!sessionIdParam || !sessionTypeParam) {
              console.error('세션 정보가 없어 결과 목록 페이지로 이동할 수 없습니다.');
              setError('세션 정보가 없습니다. 홈페이지에서 다시 시작해주세요.');
              return;
            }
            
            try {
              // 먼저 세션 상태를 확인하여 모든 아이템이 완료되었는지 검증
              const sessionData = await getTrainingSession(sessionId);
              
              // total_items와 completed_items의 값이 같은지 확인
              if (sessionData.total_items !== sessionData.completed_items) {
                
                // 같지 않으면 alert 표시 후 함수 종료
                const trainingType = sessionData.type === 'word' ? '단어' : sessionData.type === 'sentence' ? '문장' : '발성';
                toast.error(`아직 제출하지 않은 ${trainingType} 훈련이 있습니다.`);
                return;
              }
              
              // 두 값이 같으면 세션 종료 API 호출
              await completeTrainingSession(sessionId);
              
              // 세션 종료 성공 후 result-list 페이지로 이동 (sessionId와 type을 URL 파라미터로 전달)
              const resultListUrl = `/result-list?sessionId=${sessionIdParam}&type=${sessionTypeParam}`;
              
              navigate(resultListUrl);
          } catch (error: unknown) {
            console.error('세션 완료 처리 실패:', error);
              
              // 에러 상태에 따른 처리
              const enhancedError = error as { status?: number };
              if (enhancedError.status === 400) {
                // 400: 아직 모든 아이템이 완료되지 않음
                const trainingType = sessionTypeParam === 'word' ? '단어' : sessionTypeParam === 'sentence' ? '문장' : '발성';
                toast.error(`아직 제출하지 않은 ${trainingType} 훈련이 있습니다.`);
              } else if (enhancedError.status === 401) {
                // 401: 인증 필요
                toast.error('인증이 필요합니다. 다시 로그인해주세요.');
                navigate('/login');
              } else if (enhancedError.status === 404) {
                // 404: 세션을 찾을 수 없음
                toast.error('세션을 찾을 수 없습니다. 홈페이지에서 다시 시작해주세요.');
                navigate('/');
              } else {
                // 기타 에러
                const errorWithMessage = error as { message?: string };
                const errorMessage = errorWithMessage.message || '세션 종료 중 오류가 발생했습니다.';
                console.error('세션 완료 처리 실패:', errorMessage);
                toast.error(errorMessage);
              }
            }
          }
        } else {
          // training_items에서 찾지 못한 경우 (없어야 하지만 방어적 코드)
          // 최소한 is_completed는 업데이트
          setCurrentItem({
            ...currentItem,
            is_completed: true,
            video_url: response.video_url || currentItem.video_url,
          });
          
          // 기본적으로 결과 페이지 표시
          setShowResult(false);
        }
      } else {
        // response.session이 없는 경우 (없어야 하지만 방어적 코드)
        // 최소한 is_completed는 업데이트
        setCurrentItem({
          ...currentItem,
          is_completed: true,
          video_url: response.video_url || currentItem.video_url,
        });
        
        // 기본적으로 결과 페이지 표시
        setShowResult(false);
      }
      
      // 업로드 완료 후 파일 상태 초기화는 위에서 이미 처리됨 (아이템 이동 전에 초기화)
      
    } catch (err: unknown) {
      console.error('📥 영상 업로드 실패:', err);
      
      const axiosError = err as { response?: { status?: number } };
      const status = axiosError.response?.status;
      
      // 401: 인증 오류 - 강제 로그인 페이지 이동
      if (status === 401) {
        toast.error('세션이 만료되었습니다. 다시 로그인해주세요.');
        setUploadState(prev => ({ ...prev, isUploading: false }));
        setTimeout(() => {
          navigate('/login');
        }, 1500);
        return;
      }
      
      // 404: 세션 없음 - 강제 홈으로 이동
      if (status === 404) {
        toast.error('세션을 찾을 수 없습니다. 홈에서 다시 시작해주세요.');
        setUploadState(prev => ({ ...prev, isUploading: false }));
        setTimeout(() => {
          navigate('/');
        }, 1500);
        return;
      }
      
      // 422: 파일 오류 - 강제 다시 녹화
      if (status === 422) {
        toast.error('파일이 올바르지 않습니다. 다시 녹화해주세요.');
        setUploadState(prev => ({ ...prev, isUploading: false }));
        handleRetake(); // 자동으로 초기화
        return;
      }
      
      // 그 외 에러 (네트워크, 서버 오류) - 재시도 가능
      let errorMessage = '영상 업로드에 실패했습니다.';
      
      const axiosErrorWithDetail = err as { response?: { data?: { detail?: string } } };
      if (axiosErrorWithDetail.response?.data?.detail) {
        errorMessage = axiosErrorWithDetail.response.data.detail;
      }
      
      setUploadState(prev => ({ ...prev, error: errorMessage }));
    } finally {
      setUploadState(prev => ({ ...prev, isUploading: false }));
    }
  };

  const handleNextWord = async () => {
    if (!sessionIdParam || !currentItem?.has_next) return;
    
    // 단어연습 또는 문장연습인 경우, 업로드가 완료되지 않았으면 다음 단어로 이동하지 않음
    if ((sessionTypeParam === 'word' || sessionTypeParam === 'sentence') && !currentItem.is_completed) {
      return;
    }
    
    const sessionId = Number(sessionIdParam);
    if (isNaN(sessionId)) return;
    
    try {
      // 결과 페이지를 먼저 숨김 (버튼 클릭 시 즉시 처리)
      setShowResult(false);
      
      // 다음 아이템 인덱스 계산
      const nextItemIndex = (currentItem.item_index || 0) + 1;
      
      // 다음 아이템 조회
      const nextItemData = await getSessionItemByIndex(sessionId, nextItemIndex);
      
      // 모든 상태를 한 번에 배치 업데이트
      setCurrentItem(nextItemData);
      setShowResult(false);
      
      // 비디오 상태 설정
      if (nextItemData.video_url != null) {
        if (nextItemData.composited_video_url != null) {
          setVideoState({
            userVideoUrl: nextItemData.video_url,
            compositedVideoUrl: nextItemData.composited_video_url,
            compositedVideoError: null,
            isLoadingComposited: false,
          });
        } else {
          setVideoState({
            userVideoUrl: nextItemData.video_url,
            compositedVideoUrl: undefined,
            compositedVideoError: null,
            isLoadingComposited: false,
          });
        }
      } else {
        setVideoState(createInitialVideoState());
      }

      // 이전 아이템의 녹화 영상 상태 초기화
      retake(); // useMediaRecorder 상태 초기화 (blobUrl 제거)
      setUploadState(prev => ({ ...prev, file: null })); // 업로드용 파일 초기화
      
      // 세션 데이터는 이미 currentItem에 저장됨
      
      // URL 업데이트는 약간의 지연을 두어 상태 업데이트가 완료된 후 실행
      setTimeout(() => {
        updateUrl(nextItemData.item_index);
      }, 50);
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
      // 결과 페이지를 먼저 숨김 (버튼 클릭 시 즉시 처리)
      setShowResult(false);
      
      // 이전 아이템 인덱스 계산
      const prevItemIndex = (currentItem.item_index || 0) - 1;
      
      // 이전 아이템 조회
      const prevItemData = await getSessionItemByIndex(sessionId, prevItemIndex);
      
      // 모든 상태를 한 번에 배치 업데이트
      setCurrentItem(prevItemData);
      setShowResult(false);
      
      // 비디오 상태 설정
      if (prevItemData.video_url != null) {
        if (prevItemData.composited_video_url != null) {
          setVideoState({
            userVideoUrl: prevItemData.video_url,
            compositedVideoUrl: prevItemData.composited_video_url,
            compositedVideoError: null,
            isLoadingComposited: false,
          });
        } else {
          setVideoState({
            userVideoUrl: prevItemData.video_url,
            compositedVideoUrl: undefined,
            compositedVideoError: null,
            isLoadingComposited: false,
          });
        }
      } else {
        setVideoState(createInitialVideoState());
      }

      // 이전 아이템의 녹화 영상 상태 초기화
      retake(); // useMediaRecorder 상태 초기화 (blobUrl 제거)
      setUploadState(prev => ({ ...prev, file: null })); // 업로드용 파일 초기화
      
      // 세션 데이터는 이미 currentItem에 저장됨
      
      // URL 업데이트는 약간의 지연을 두어 상태 업데이트가 완료된 후 실행
      setTimeout(() => {
        updateUrl(prevItemData.item_index);
      }, 50);
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
    <>
      <TrainingLayout
        key={`${sessionIdParam}-${sessionTypeParam}`}
        currentItem={currentItem}
        sessionData={sessionData}
        onNext={handleNextWord}
        onPrevious={handlePreviousWord}
        recordingState={recordingState}
      >
        {showResult ? (
          <ResultComponent 
            sessionId={sessionIdParam ? Number(sessionIdParam) : undefined}
            sessionType={sessionTypeParam || undefined}
            userVideoUrl={videoState.userVideoUrl}
            compositedVideoUrl={videoState.compositedVideoUrl}
            isLoadingCompositedVideo={videoState.isLoadingComposited}
            compositedVideoError={videoState.compositedVideoError}
            onNext={handleNextWord}
            hasNext={currentItem?.has_next ?? false}
            onRetake={handleRetake}
            isUploading={uploadState.isUploading}
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
            isUploading={uploadState.isUploading}
            uploadError={uploadState.error}
            isCameraReady={!!isCameraReady}
            videoRef={videoRef}
          />
        )}
      </TrainingLayout>
    </>
  );
};

export default PracticePage;