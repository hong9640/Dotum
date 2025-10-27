import axios from "axios";

// Base URL 설정 (환경 변수 또는 기본값)
const API_BASE_URL = import.meta.env.VITE_BASE_URL;

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
    // 요청 전에 토큰 등을 추가할 수 있습니다
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 응답 인터셉터
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // 에러 처리 로직
    return Promise.reject(error);
  }
);

