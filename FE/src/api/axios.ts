import axios from "axios";
import { getCookie, setCookie } from "@/utils/cookies";

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

// 토큰 갱신 중 플래그
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value: unknown) => void;
  reject: (reason?: unknown) => void;
}> = [];

// 대기 중인 요청 처리
const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

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

// 응답 인터셉터 (자동 토큰 갱신)
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    // 401 에러이고, 재시도하지 않은 요청인 경우
    if (error.response?.status === 401 && !originalRequest._retry) {
      // 토큰 갱신 API 자체가 실패한 경우
      if (originalRequest.url?.includes('/auth/token')) {
        isRefreshing = false;
        processQueue(error, null);
        return Promise.reject(error);
      }
      
      // 로그인/회원가입 API는 토큰 갱신 시도하지 않음
      if (originalRequest.url?.includes('/auth/login') || 
          originalRequest.url?.includes('/auth/signup')) {
        return Promise.reject(error);
      }

      // 이미 토큰 갱신 중이면 대기열에 추가
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return apiClient(originalRequest);
          })
          .catch((err) => {
            return Promise.reject(err);
          });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        // 리프레시 토큰으로 액세스 토큰 갱신 시도
        const response = await apiClient.post("/auth/token", {}, {
          headers: { Accept: "application/json" },
        });

        const { access_token, expires_in } = response.data;
        
        // 새 토큰 저장
        const expiresInDays = expires_in / (24 * 60 * 60);
        setCookie('access_token', access_token, expiresInDays);

        // 대기 중인 요청들 처리
        processQueue(null, access_token);
        isRefreshing = false;

        // 원래 요청 재시도
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        // 리프레시 토큰도 만료된 경우
        processQueue(refreshError, null);
        isRefreshing = false;
        
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

