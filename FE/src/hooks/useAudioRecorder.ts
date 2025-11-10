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
  const streamRef = useRef<MediaStream | null>(null);  // ref로도 보관
  const audioContextRef = useRef<AudioContext | null>(null);  // ref로도 보관

  const startRecording = useCallback(async () => {
    try {
      // 이전 AudioContext 정리 (혹시 남아있다면)
      const prevContext = audioContextRef.current;
      if (prevContext && prevContext.state !== 'closed') {
        await prevContext.close();
        audioContextRef.current = null;
        setAudioContext(null);
        setAnalyser(null);
      }
      
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
      streamRef.current = mediaStream;
      setStream(mediaStream);
      
      // AudioContext 및 AnalyserNode 생성
      const ctx = new AudioContext();
      audioContextRef.current = ctx;
      const source = ctx.createMediaStreamSource(mediaStream);
      const analyserNode = ctx.createAnalyser();
      
      analyserNode.fftSize = 2048;
      analyserNode.smoothingTimeConstant = 0;
      
      source.connect(analyserNode);
      
      setAudioContext(ctx);
      setAnalyser(analyserNode);
      
      // RecordRTC로 WAV 녹음
      const recorder = new RecordRTC(mediaStream, {
        type: 'audio',
        mimeType: 'audio/wav',
        recorderType: RecordRTC.StereoAudioRecorder,
        numberOfAudioChannels: 1,
        desiredSampRate: 16000,
        timeSlice: 1000,
        ondataavailable: () => {}
      });
      
      recorderRef.current = recorder;
      recorder.startRecording();
      setIsRecording(true);
    } catch (error) {
      console.error('마이크 접근 오류:', error);
      alert('마이크 접근 권한이 필요합니다.');
    }
  }, []);

  const stopRecording = useCallback(() => {
    if (recorderRef.current && isRecording) {
      // 즉시 stream 정리 (마이크 표시 끄기)
      const currentStream = streamRef.current;
      if (currentStream) {
        currentStream.getTracks().forEach(track => track.stop());
        streamRef.current = null;
        setStream(null);
      }
      
      // AudioContext도 즉시 닫기
      const currentContext = audioContextRef.current;
      if (currentContext && currentContext.state !== 'closed') {
        currentContext.close().catch(err => console.warn('AudioContext 정리 실패:', err));
        audioContextRef.current = null;
        setAudioContext(null);
        setAnalyser(null);
      }
      
      const recorder = recorderRef.current;
      recorder.stopRecording(() => {
        const blob = recorder.getBlob();
        const url = URL.createObjectURL(blob);
        
        setAudioBlob(blob);
        setAudioUrl(url);
        
        recorder.destroy();
        recorderRef.current = null;
        setIsRecording(false);
      });
    }
  }, [isRecording]);

  const reset = useCallback(() => {
    if (recorderRef.current && isRecording) {
      recorderRef.current.stopRecording(() => {
        recorderRef.current?.destroy();
        recorderRef.current = null;
      });
      setIsRecording(false);
    }
    
    const currentStream = streamRef.current;
    if (currentStream) {
      currentStream.getTracks().forEach(track => track.stop());
      streamRef.current = null;
      setStream(null);
    }
    
    const currentContext = audioContextRef.current;
    if (currentContext && currentContext.state !== 'closed') {
      currentContext.close();
      audioContextRef.current = null;
      setAudioContext(null);
      setAnalyser(null);
    }
    
    setAudioBlob(null);
    setAudioUrl(null);
    recorderRef.current = null;
  }, [isRecording]);

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

