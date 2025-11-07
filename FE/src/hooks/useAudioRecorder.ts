import { useState, useRef, useCallback } from 'react';
import RecordRTC from 'recordrtc';

export interface UseAudioRecorderReturn {
  isRecording: boolean;
  audioBlob: Blob | null;
  audioUrl: string | null;
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  reset: () => void;
  stream: MediaStream | null;
  analyser: AnalyserNode | null;
  audioContext: AudioContext | null;
}

export function useAudioRecorder(): UseAudioRecorderReturn {
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [analyser, setAnalyser] = useState<AnalyserNode | null>(null);
  const [audioContext, setAudioContext] = useState<AudioContext | null>(null);
  
  const recorderRef = useRef<RecordRTC | null>(null);

  const startRecording = useCallback(async () => {
    try {
      // 기존 녹음 데이터 초기화
      setAudioBlob(null);
      setAudioUrl(null);
      
      const mediaStream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100
        } 
      });
      setStream(mediaStream);
      
      // AudioContext 및 AnalyserNode 생성
      const ctx = new AudioContext();
      const source = ctx.createMediaStreamSource(mediaStream);
      const analyserNode = ctx.createAnalyser();
      
      analyserNode.fftSize = 2048;
      analyserNode.smoothingTimeConstant = 0;
      
      source.connect(analyserNode);
      // 주의: destination에 연결하지 않음 (에코 방지)
      
      setAudioContext(ctx);
      setAnalyser(analyserNode);
      
      // RecordRTC를 사용해서 WAV 녹음
      console.log('🎙️ RecordRTC로 WAV 녹음 시작');
      
      const recorder = new RecordRTC(mediaStream, {
        type: 'audio',
        mimeType: 'audio/wav',
        recorderType: RecordRTC.StereoAudioRecorder,
        numberOfAudioChannels: 1, // 모노
        desiredSampRate: 16000, // Praat에 적합한 샘플레이트
        timeSlice: 1000,
        ondataavailable: () => {
          // 실시간 데이터 처리 (필요시)
        }
      });
      
      recorderRef.current = recorder;
      recorder.startRecording();
      setIsRecording(true);
    } catch (error) {
      console.error('Error accessing microphone:', error);
      alert('마이크 접근 권한이 필요합니다.');
    }
  }, []);

  const stopRecording = useCallback(() => {
    if (recorderRef.current && isRecording) {
      recorderRef.current.stopRecording(() => {
        const blob = recorderRef.current!.getBlob();
        const url = URL.createObjectURL(blob);
        
        console.log('✅ WAV 녹음 완료:', {
          type: blob.type,
          size: `${(blob.size / 1024).toFixed(2)} KB`
        });
        
        setAudioBlob(blob);
        setAudioUrl(url);
        
        // Clean up
        if (stream) {
          stream.getTracks().forEach(track => track.stop());
          setStream(null);
        }
        
        // AudioContext cleanup
        if (audioContext && audioContext.state !== 'closed') {
          audioContext.close();
        }
        setAudioContext(null);
        setAnalyser(null);
      });
      
      setIsRecording(false);
    }
  }, [isRecording, stream, audioContext]);

  const reset = useCallback(() => {
    // 녹음 중이면 중지
    if (recorderRef.current && isRecording) {
      recorderRef.current.stopRecording(() => {
        recorderRef.current?.destroy();
        recorderRef.current = null;
      });
      setIsRecording(false);
    }
    
    // 스트림 정리
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
    }
    
    // AudioContext 정리
    if (audioContext && audioContext.state !== 'closed') {
      audioContext.close();
      setAudioContext(null);
      setAnalyser(null);
    }
    
    // 상태 초기화
    setAudioBlob(null);
    setAudioUrl(null);
    recorderRef.current = null;
  }, [isRecording, stream, audioContext]);

  return {
    isRecording,
    audioBlob,
    audioUrl,
    startRecording,
    stopRecording,
    reset,
    stream,
    analyser,
    audioContext,
  };
}

