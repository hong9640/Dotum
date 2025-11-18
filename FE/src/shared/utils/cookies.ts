/**
 * 쿠키 관련 유틸리티 함수들
 */

/**
 * 쿠키 설정
 * @param name 쿠키 이름
 * @param value 쿠키 값
 * @param days 만료일 (기본값: 7일)
 * @param secure HTTPS에서만 전송 (기본값: true)
 * @param httpOnly JavaScript에서 접근 불가 (기본값: false)
 */
export const setCookie = (
  name: string,
  value: string,
  days: number = 7,
  secure: boolean = true,
  httpOnly: boolean = false
): void => {
  const expires = new Date();
  expires.setTime(expires.getTime() + days * 24 * 60 * 60 * 1000);
  
  let cookieString = `${name}=${value}; expires=${expires.toUTCString()}; path=/`;
  
  if (secure && window.location.protocol === 'https:') {
    cookieString += '; secure';
  }
  
  if (httpOnly) {
    cookieString += '; httpOnly';
  }
  
  // SameSite 설정 (CSRF 공격 방지)
  cookieString += '; samesite=strict';
  
  document.cookie = cookieString;
};

/**
 * 쿠키 값 가져오기
 * @param name 쿠키 이름
 * @returns 쿠키 값 또는 null
 */
export const getCookie = (name: string): string | null => {
  const nameEQ = name + "=";
  const ca = document.cookie.split(';');
  
  for (let i = 0; i < ca.length; i++) {
    let c = ca[i];
    while (c.charAt(0) === ' ') c = c.substring(1, c.length);
    if (c.indexOf(nameEQ) === 0) {
      const value = c.substring(nameEQ.length, c.length);
      return value;
    }
  }
  return null;
};

/**
 * 쿠키 삭제
 * @param name 쿠키 이름
 */
export const deleteCookie = (name: string): void => {
  document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; samesite=strict`;
};

/**
 * 모든 인증 관련 쿠키 삭제
 * (refresh_token은 서버 HttpOnly 쿠키이므로 로그아웃 API에서 처리)
 */
export const clearAuthCookies = (): void => {
  deleteCookie('access_token');
  // refresh_token은 서버에서 HttpOnly 쿠키로 설정되어 있어
  // 클라이언트에서 삭제 불가능 (로그아웃 API에서 처리)
};

/**
 * 인증 토큰이 존재하는지 확인
 * @returns 토큰 존재 여부
 */
export const hasAuthToken = (): boolean => {
  const token = getCookie('access_token');
  return !!token;
};
