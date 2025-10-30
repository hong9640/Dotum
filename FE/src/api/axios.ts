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
  withCredentials: true, // 모든 요청에 쿠키 포함 (CORS 지원)
});


// 요청 인터셉터
apiClient.interceptors.request.use(
  (config) => {
    // 쿠키에서 토큰 가져오기
    const token = getCookie('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
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
    return response;
  },
  (error) => {
    return Promise.reject(error);
  }
);

