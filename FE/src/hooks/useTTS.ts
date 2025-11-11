import { useState, useEffect, useCallback, useRef } from 'react';
import { stopAllTTS } from '@/utils/tts';

interface UseTTSOptions {
  lang?: string;
  rate?: number;
  pitch?: number;
  volume?: number;
}

interface UseTTSReturn {
  speak: (text: string) => void;
  stop: () => void;
  isSpeaking: boolean;
  isSupported: boolean;
}

/**
 * Web Speech API를 사용한 TTS(Text-to-Speech) 커스텀 훅
 * 
 * @param options - TTS 옵션 (언어, 속도, 음높이, 볼륨)
 * @returns speak, stop 함수와 상태 정보
 */
export const useTTS = (options: UseTTSOptions = {}): UseTTSReturn => {
  const {
    lang = 'ko-KR',
    rate = 0.9,
    pitch = 1,
    volume = 1,
  } = options;

  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isSupported, setIsSupported] = useState(false);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  useEffect(() => {
    // Web Speech API 지원 여부 확인
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      setIsSupported(true);
    }

    // 컴포넌트 언마운트 시 음성 중지
    return () => {
      if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const speak = useCallback(
    (text: string) => {
      if (!isSupported || !text) return;

      // 이미 재생 중인 경우 중지
      if (window.speechSynthesis.speaking) {
        window.speechSynthesis.cancel();
      }

      // 새 발화 생성
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = lang;
      utterance.rate = rate;
      utterance.pitch = pitch;
      utterance.volume = volume;

      // 이벤트 핸들러
      utterance.onstart = () => {
        setIsSpeaking(true);
      };

      utterance.onend = () => {
        setIsSpeaking(false);
      };

      utterance.onerror = (event) => {
        console.error('TTS 에러:', event);
        setIsSpeaking(false);
      };

      utteranceRef.current = utterance;
      window.speechSynthesis.speak(utterance);
    },
    [isSupported, lang, rate, pitch, volume]
  );

  const stop = useCallback(() => {
    if (isSupported) {
      stopAllTTS();
      setIsSpeaking(false);
    }
  }, [isSupported]);

  return {
    speak,
    stop,
    isSpeaking,
    isSupported,
  };
};
