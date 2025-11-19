/**
 * 날짜 포맷팅 유틸리티 함수들
 */

/**
 * 날짜를 "YYYY년 MM월 DD일 완료" 형식으로 포맷팅
 * @param dateString - ISO 8601 형식의 날짜 문자열
 * @returns 포맷팅된 날짜 문자열
 */
export const formatDate = (dateString: string): string => {
  try {
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    
    return `${year}년 ${month}월 ${day}일 완료`;
  } catch (error) {
    console.error('날짜 포맷팅 실패:', error);
    return '날짜 정보 없음';
  }
};

/**
 * 날짜를 "YYYY년 MM월 DD일" 형식으로 포맷팅 (완료 없이)
 * @param dateString - ISO 8601 형식의 날짜 문자열
 * @returns 포맷팅된 날짜 문자열
 */
export const formatDateOnly = (dateString: string): string => {
  try {
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    
    return `${year}년 ${month}월 ${day}일`;
  } catch (error) {
    console.error('날짜 포맷팅 실패:', error);
    return '날짜 정보 없음';
  }
};

/**
 * 날짜와 시간을 "YYYY년 MM월 DD일 HH:mm" 형식으로 포맷팅
 * @param dateString - ISO 8601 형식의 날짜 문자열
 * @returns 포맷팅된 날짜/시간 문자열
 */
export const formatDateTime = (dateString: string): string => {
  try {
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    
    return `${year}년 ${month}월 ${day}일 ${hours}:${minutes}`;
  } catch (error) {
    console.error('날짜/시간 포맷팅 실패:', error);
    return '날짜 정보 없음';
  }
};

/**
 * 상대 시간 포맷팅 (예: "3분 전", "2시간 전")
 * @param dateString - ISO 8601 형식의 날짜 문자열
 * @returns 상대 시간 문자열
 */
export const formatRelativeTime = (dateString: string): string => {
  try {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return '방금 전';
    if (diffMins < 60) return `${diffMins}분 전`;
    if (diffHours < 24) return `${diffHours}시간 전`;
    if (diffDays < 7) return `${diffDays}일 전`;
    
    return formatDateOnly(dateString);
  } catch (error) {
    console.error('상대 시간 포맷팅 실패:', error);
    return '날짜 정보 없음';
  }
};

/**
 * 날짜를 한국어 형식으로 포맷팅 (예: "2025년 1월 13일")
 * @param dateString - ISO 8601 형식의 날짜 문자열
 * @returns 한국어 형식의 날짜 문자열
 */
export const formatDateKorean = (dateString: string): string => {
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  } catch (error) {
    console.error('날짜 포맷팅 실패:', error);
    return '날짜 정보 없음';
  }
};

