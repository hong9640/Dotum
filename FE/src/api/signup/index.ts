import { apiClient } from "../axios";
import type { AxiosErrorResponse } from "@/types/api";

// 회원가입 API 타입 정의
export interface SignupRequest {
  username: string;
  password: string;
}

export interface SignupResponse {
  status: "SUCCESS" | "FAILURE";
  error?: {
    code: string;
    message: string;
  };
}

// 이메일 중복 확인 API 타입 정의
export interface EmailCheckResponse {
  status: "SUCCESS" | "Duplicate";
  data: {
    email: string;
    is_duplicate: boolean;
    message: string;
  };
}

// 에러 매핑 테이블
const ERROR_MAPPING: Record<string, string> = {
  USERNAME_ALREADY_EXISTS: "이미 등록된 이메일입니다.",
};

/**
 * 회원가입 API 호출
 * @param data 회원가입 폼 데이터
 * @returns 회원가입 결과
 */
export const Signup = async (
  data: SignupRequest
): Promise<SignupResponse> => {
  try {
    const response = await apiClient.post<SignupResponse>("/auth/signup", {
      username: data.username,
      password: data.password,
      name: ""
    });

    return response.data;
  } catch (error: unknown) {
    // HTTP 에러 응답 (4xx, 5xx)인 경우 에러 응답 반환
    const axiosError = error as AxiosErrorResponse & { response?: { data?: SignupResponse } };
    if (axiosError.response?.data) {
      return axiosError.response.data;
    }
    // 네트워크 에러 등
    throw error;
  }
};

/**
 * 이메일 중복 확인 API 호출
 * @param email 확인할 이메일 주소
 * @returns 이메일 중복 확인 결과
 */
export const CheckEmailDuplication = async (
  email: string
): Promise<EmailCheckResponse> => {
  try {
    const response = await apiClient.get<EmailCheckResponse>(
      `/auth/emails/${email}`
    );

    return response.data;
  } catch (error: unknown) {
    // HTTP 에러 응답 (4xx, 5xx)인 경우 에러 응답 반환
    const axiosError = error as AxiosErrorResponse & { response?: { data?: EmailCheckResponse } };
    if (axiosError.response?.data) {
      return axiosError.response.data;
    }
    // 네트워크 에러 등
    throw error;
  }
};

/**
 * API 에러 코드를 사용자 친화적인 메시지로 변환
 * @param errorCode API 에러 코드
 * @param defaultMessage 기본 에러 메시지
 * @returns 사용자 친화적인 에러 메시지
 */
export const GetErrorMessage = (
  errorCode?: string,
  defaultMessage: string = "회원가입에 실패했습니다."
): string => {
  if (!errorCode) return defaultMessage;
  
  return ERROR_MAPPING[errorCode] || defaultMessage;
};

