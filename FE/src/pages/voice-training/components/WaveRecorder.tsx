import React, { useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { RotateCcw, Upload } from 'lucide-react';
import { useAudioRecorder } from '@/hooks/useAudioRecorder';
import RecordToggle from './RecordToggle';
import StatusBadge from './StatusBadge';
import AudioPlayer from './AudioPlayer';
import AudioLevelGraph, { type AudioLevelGraphRef } from './AudioLevelGraph';

interface WaveRecorderProps {
  onRecordEnd?: (blob: Blob, url: string) => void;
  onSubmit?: (audioBlob: Blob, graphImageBlob: Blob) => void;
  isSubmitting?: boolean;
  resetTrigger?: number; // 리셋 트리거 (값이 변경되면 리셋)
}

const WaveRecorder: React.FC<WaveRecorderProps> = ({ 
  onRecordEnd, 
  onSubmit,
  isSubmitting = false,
  resetTrigger = 0
}) => {
  const { isRecording, audioBlob, audioUrl, startRecording, stopRecording, reset, analyser } = useAudioRecorder();
  const graphRef = useRef<AudioLevelGraphRef>(null);
  
  // resetTrigger가 변경되면 리셋
  React.useEffect(() => {
    if (resetTrigger > 0) {
      reset();
    }
  }, [resetTrigger, reset]);

  useEffect(() => {
    if (audioBlob && audioUrl) {
      onRecordEnd?.(audioBlob, audioUrl);
    }
  }, [audioBlob, audioUrl, onRecordEnd]);

  const handleToggle = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const handleRetake = () => {
    // 녹음 재시작
    startRecording();
  };

  const handleSubmit = async () => {
    if (!audioBlob || !onSubmit) return;
    
    // 그래프 이미지 캡처
    const graphImageBlob = await graphRef.current?.captureImage();
    if (!graphImageBlob) {
      console.error('그래프 이미지 캡처 실패');
      return;
    }
    
    onSubmit(audioBlob, graphImageBlob);
  };

  return (
    <div className="space-y-6">
      <AudioLevelGraph
        ref={graphRef}
        active={isRecording}
        analyser={analyser}
        width={720}
        height={200}
        stroke="#0C2C66"
        minDb={-60}
        maxDb={0}
      />

      <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
        <StatusBadge label={isRecording ? "녹음 중" : "대기 중"} active={isRecording} />
        
        {!audioUrl ? (
          <RecordToggle isRecording={isRecording} onToggle={handleToggle} />
        ) : (
          <div className="flex flex-wrap items-center gap-3">
            <Button 
              size="lg" 
              variant="secondary" 
              className="px-8 py-6 text-xl flex items-center gap-3" 
              onClick={handleRetake}
              disabled={isSubmitting}
            >
              <RotateCcw className="size-6 text-slate-700" strokeWidth={2.5} />
              다시 녹음
            </Button>
            
            {onSubmit && (
              <Button 
                size="lg" 
                variant="default" 
                className="px-8 py-6 text-xl flex items-center gap-3" 
                onClick={handleSubmit}
                disabled={isSubmitting || !audioBlob}
              >
                <Upload className="size-6 text-white" strokeWidth={2.5} />
                {isSubmitting ? "제출 중..." : "제출하기"}
              </Button>
            )}
          </div>
        )}
      </div>

      <AudioPlayer src={audioUrl} />
    </div>
  );
};

export default WaveRecorder;

