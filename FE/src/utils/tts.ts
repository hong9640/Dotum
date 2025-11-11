/**
 * TTS(Text-to-Speech) 유틸리티 함수
 */

/**
 * 현재 재생 중인 모든 TTS를 즉시 중지합니다.
 */
export const stopAllTTS = (): void => {
  if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
    window.speechSynthesis.cancel();
  }
};

