import React, { useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { RotateCcw, Upload, Loader2 } from 'lucide-react';
import { useAudioRecorder } from '@/hooks/useAudioRecorder';
import { useMediaQuery } from '@/hooks/useMediaQuery'; // 1. 훅 임포트
import RecordToggle from './RecordToggle';
import AudioPlayer from './AudioPlayer';
import AudioLevelGraph, { type AudioLevelGraphRef } from './AudioLevelGraph';

interface WaveRecorderProps {
  onRecordEnd?: (blob: Blob, url: string) => void;
  onSubmit?: (audioBlob: Blob, graphImageBlob: Blob) => void;
  isSubmitting?: boolean;
  isLastSubmit?: boolean; // 마지막 제출 여부 (메시지 변경용)
  resetTrigger?: number; // 리셋 트리거 (값이 변경되면 리셋)
}

const WaveRecorder: React.FC<WaveRecorderProps> = ({ 
  onRecordEnd, 
  onSubmit,
  isSubmitting = false,
  isLastSubmit = false,
  resetTrigger = 0
}) => {
  const { 
    isRecording, 
    audioBlob, 
    audioUrl, 
    startRecording, 
    stopRecording, 
    reset,
    analyser
  } = useAudioRecorder();
  const graphRef = useRef<AudioLevelGraphRef>(null);
  const prevResetTriggerRef = useRef(resetTrigger);
  
  // 2. 브레이크포인트 감지
  // Tailwind의 'sm' (640px)을 기준으로 모바일/데스크탑 구분
  const isDesktop = useMediaQuery('(min-width: 640px)'); 
  
  // 3. 뷰포트 크기에 따라 캔버스 너비 결정
  // 데스크탑은 720px, 모바일은 340px (또는 원하는 다른 값)
  const canvasWidth = isDesktop ? 720 : 340;
  
  // resetTrigger가 변경되면 리셋 (이전 값과 다를 때만)
  React.useEffect(() => {
    if (resetTrigger > 0 && resetTrigger !== prevResetTriggerRef.current) {
      reset();
      prevResetTriggerRef.current = resetTrigger;
    }
  }, [resetTrigger, reset]);

  useEffect(() => {
    if (audioBlob && audioUrl) {
      onRecordEnd?.(audioBlob, audioUrl);
    }
  }, [audioBlob, audioUrl, onRecordEnd]);
  
  // 컴포넌트 언마운트 시 모든 리소스 정리
  useEffect(() => {
    return () => {
      reset();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleToggle = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const handleRetake = () => {
    startRecording();
  };

  const handleSubmit = async () => {
    if (!audioBlob || !onSubmit) return;
    
    const graphImageBlob = await graphRef.current?.captureImage();
    if (!graphImageBlob) {
      console.error('그래프 이미지 캡처 실패');
      return;
    }
    
    onSubmit(audioBlob, graphImageBlob);
    
    // 제출 후 canvas 초기화
    graphRef.current?.clearCanvas();
  };

  return (
    <div className="relative space-y-6">
      {/* 제출 중 로딩 오버레이 (모든 제출 시 표시) */}
      {isSubmitting && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="bg-white rounded-2xl shadow-2xl p-10 max-w-md mx-4 text-center animate-in zoom-in-95 duration-300">
            <div className="mb-6 flex justify-center">
              {/* 로딩 스피너 */}
              <div className="relative">
                <div className="w-20 h-20 border-4 border-lime-200 rounded-full"></div>
                <div className="absolute inset-0 w-20 h-20 border-4 border-transparent border-t-lime-500 rounded-full animate-spin"></div>
                <Loader2 className="absolute inset-0 m-auto w-10 h-10 text-lime-600 animate-pulse" />
              </div>
            </div>
            
            {/* 마지막 제출 시와 그 외 제출 시 메시지 분기 */}
            {isLastSubmit ? (
              <>
                <h3 className="text-3xl font-bold text-gray-900 mb-3">결과를 계산 중입니다</h3>
                <p className="text-gray-600 text-lg mb-6">잠시만 기다려주세요...</p>
                <div className="bg-lime-50 border border-lime-200 rounded-lg p-4">
                  <p className="text-gray-700 text-sm">
                    🎤 음성 분석 (Praat)<br/>
                    📊 파형 데이터 처리<br/>
                    ✨ 평가 결과 생성
                  </p>
                </div>
              </>
            ) : (
              <>
                <h3 className="text-3xl font-bold text-gray-900 mb-3">제출 중...</h3>
                <p className="text-gray-600 text-lg">음성을 분석하고 있습니다</p>
              </>
            )}
          </div>
        </div>
      )}
      
      {/* 제출 중일 때는 메인 콘텐츠 비활성화 (시각적으로는 보이게) */}
      <div className={isSubmitting ? 'pointer-events-none opacity-30' : ''}>
        {/* 4. 캔버스를 감싸서 가운데 정렬 (선택 사항이지만 권장) */}
          <AudioLevelGraph
            ref={graphRef}
            active={isRecording}
            analyser={analyser}
            // 5. 동적으로 계산된 너비 전달
            width={canvasWidth} 
            height={200}
            stroke="#0C2C66"
            minDb={-60}
            maxDb={0}
          />

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mt-4">
          {!audioUrl ? (
            <RecordToggle isRecording={isRecording} onToggle={handleToggle} />
          ) : (
            <div className="flex flex-wrap items-center justify-center gap-3">
              <Button 
                size="lg" 
                variant="secondary" 
                className="px-5 sm:px-8 py-4 sm:py-6 text-lg sm:text-xl flex items-center gap-3" 
                onClick={handleRetake}
                disabled={isSubmitting}
              >
                <RotateCcw className="sm:size-6 size-5 text-slate-700" strokeWidth={2.5} />
                다시 녹음
              </Button>
              
              {onSubmit && (
                <Button 
                  size="lg" 
                  variant="default" 
                  className="px-5 sm:px-8 py-4 sm:py-6 text-lg sm:text-xl flex items-center gap-3" 
                  onClick={handleSubmit}
                  disabled={isSubmitting || !audioBlob}
                >
                  <Upload className="sm:size-6 size-5 text-white" strokeWidth={2.5} />
                  제출하기
                </Button>
              )}
            </div>
          )}
        </div>

      <AudioPlayer src={audioUrl} />
      </div>
    </div>
  );
};

export default WaveRecorder;

