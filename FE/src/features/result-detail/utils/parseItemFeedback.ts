/**
 * 아이템 피드백 파싱 유틸리티
 */

export interface ItemFeedback {
  item?: string; // 한 줄 요약
  vowel_distortion?: string; // 모음 왜곡도
  sound_stability?: string; // 소리의 안정도
  voice_clarity?: string; // 음성 일탈도
  voice_health?: string; // 음성 건강지수
}

/**
 * feedback 문자열을 파싱하여 ItemFeedback 객체로 변환
 * @param feedbackString feedback JSON 문자열 또는 null/undefined
 * @returns 파싱된 ItemFeedback 객체 또는 null
 */
export function parseItemFeedback(feedbackString: string | null | undefined): ItemFeedback | null {
  if (!feedbackString) {
    return null;
  }

  try {
    // JSON 문자열인 경우 파싱
    const parsed = typeof feedbackString === 'string' 
      ? JSON.parse(feedbackString) 
      : feedbackString;
    
    // ItemFeedback 타입 검증
    if (typeof parsed === 'object' && parsed !== null) {
      return {
        item: parsed.item || undefined,
        vowel_distortion: parsed.vowel_distortion || undefined,
        sound_stability: parsed.sound_stability || undefined,
        voice_clarity: parsed.voice_clarity || undefined,
        voice_health: parsed.voice_health || undefined,
      };
    }
    
    return null;
  } catch (error) {
    console.error('피드백 파싱 실패:', error);
    // 파싱 실패 시 문자열 그대로 item으로 사용
    return {
      item: feedbackString,
    };
  }
}

