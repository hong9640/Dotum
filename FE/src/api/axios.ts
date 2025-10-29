import axios from "axios";
import { getCookie } from "@/lib/cookies";

// Base URL 설정 (환경 변수 또는 기본값)
const API_BASE_URL = import.meta.env.VITE_BASE_URL || "http://localhost:8000/api/v1";

// Axios 인스턴스 생성
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});


// 요청 인터셉터
apiClient.interceptors.request.use(
  (config) => {
    // 쿠키에서 토큰 가져오기
    const token = getCookie('access_token');
    console.log('🔑 토큰 확인:', token ? '토큰 존재' : '토큰 없음');
    console.log('📡 요청 URL:', config.url);
    console.log('📡 요청 메서드:', config.method?.toUpperCase());
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log('✅ Authorization 헤더 추가됨');
    } else {
      console.warn('⚠️ 토큰이 없어서 인증 헤더를 추가하지 않음');
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 응답 인터셉터
apiClient.interceptors.response.use(
  (response) => {
    console.log('✅ 응답 성공:', response.status, response.config.url);
    return response;
  },
  (error) => {
    console.error('❌ API 에러:', {
      status: error.response?.status,
      statusText: error.response?.statusText,
      url: error.config?.url,
      method: error.config?.method?.toUpperCase(),
      data: error.response?.data,
      headers: error.config?.headers
    });
    
    // 400 에러인 경우 요청 데이터도 로깅
    if (error.response?.status === 400) {
      console.error('📝 400 Bad Request - 요청 데이터:', error.config?.data);
      console.error('📝 서버 응답 상세:', error.response?.data);
    }
    
    // 401 에러인 경우 토큰 관련 안내
    if (error.response?.status === 401) {
      console.warn('🔐 401 Unauthorized - 토큰이 유효하지 않거나 만료되었을 수 있습니다.');
      console.log('현재 저장된 토큰:', getCookie('access_token'));
    }
    
    return Promise.reject(error);
  }
);

