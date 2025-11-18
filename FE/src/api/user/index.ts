import { apiClient } from "../axios";
import type { AxiosErrorResponse } from "@/types/api";

// 사용자 정보 응답 타입
export interface UserMeResponse {
  user_id: number;
  email: string;
  username: string;
  created_at: string;
}

/**
 * 현재 로그인한 사용자 정보 조회 API
 * @returns 사용자 정보
 */
export const getUserMe = async (): Promise<UserMeResponse> => {
  const response = await apiClient.get<UserMeResponse>("/user/me", {
    headers: {
      Accept: "application/json",
    },
  });

  return response.data;
};

/**
 * 리프레시 토큰으로 액세스 토큰 갱신
 */
export const refreshAccessToken = async () => {
  const response = await apiClient.post("/auth/token", {}, {
    headers: {
      Accept: "application/json",
    },
  });
  return response.data;
};

/**
 * 로그인 상태 확인 (리다이렉트 없이)
 * @returns 로그인 여부
 */
export const checkAuthStatus = async (): Promise<boolean> => {
  try {
    // 1단계: /user/me 호출
    await getUserMe();
    return true;
    } catch (error: unknown) {
    const axiosError = error as AxiosErrorResponse;
    // 401이 아니면 false 반환
    if (axiosError.response?.status !== 401) {
      return false;
    }

    try {
      // 2단계: 리프레시 토큰으로 갱신 시도
      await refreshAccessToken();
      
      // 갱신 성공하면 다시 user/me 호출
      await getUserMe();
      return true;
    } catch {
      // 리프레시도 실패하면 false
      return false;
    }
  }
};







