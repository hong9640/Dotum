import { useState, useEffect, useCallback, useRef } from 'react';
import { stopAllTTS } from '@/shared/utils/tts';

interface UseTTSOptions {
  lang?: string;
  rate?: number;
  pitch?: number;
  volume?: number;
}

interface UseTTSReturn {
  speak: (text: string) => void;
  speakWithIntro: (text: string, type?: 'word' | 'sentence' | 'vocal') => void;
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

  const speakWithIntro = useCallback(
    (text: string, type: 'word' | 'sentence' | 'vocal' = 'word') => {
      if (!isSupported || !text || isSpeaking) return;

      // 이미 재생 중인 경우 중지
      if (window.speechSynthesis.speaking) {
        window.speechSynthesis.cancel();
      }

      setIsSpeaking(true);

      // 안내 멘트 결정
      const isSentence = type === 'sentence' || text.includes(' ') || text.length > 10;
      const introText = isSentence 
        ? "다음 문장을 정확하게 읽어주세요" 
        : "다음 단어를 정확하게 읽어주세요";

      // 첫 번째 발화 (안내 멘트)
      const utterance1 = new SpeechSynthesisUtterance(introText);
      utterance1.lang = lang;
      utterance1.rate = rate;
      utterance1.pitch = pitch;
      utterance1.volume = volume;

      // 안내 멘트 종료 후 단어/문장 재생
      utterance1.onend = () => {
        setTimeout(() => {
          const utterance2 = new SpeechSynthesisUtterance(text);
          utterance2.lang = lang;
          utterance2.rate = rate;
          utterance2.pitch = pitch;
          utterance2.volume = volume;

          utterance2.onend = () => {
            setIsSpeaking(false);
          };

          utterance2.onerror = () => {
            setIsSpeaking(false);
          };

          window.speechSynthesis.speak(utterance2);
        }, 200); // 0.2초 대기
      };

      utterance1.onerror = () => {
        setIsSpeaking(false);
      };

      window.speechSynthesis.speak(utterance1);
    },
    [isSupported, isSpeaking, lang, rate, pitch, volume]
  );

  return {
    speak,
    speakWithIntro,
    stop,
    isSpeaking,
    isSupported,
  };
};
