import { apiClient } from "@/shared/api/axios";
import type { AxiosErrorResponse } from "@/shared/types/api";

export interface LoginRequest {
    username: string;
    password: string;
}

// 응답 토큰 정보 (refresh_token은 쿠키로 받음)
export interface TokenInfo {
    access_token: string;
    token_type: string;
    expires_in: number;
}

// 응답 사용자 정보
export interface UserInfo {
    id: number;
    username: string;
    name: string;
    role: string;
}

// 로그인 성공 응답 타입
export interface LoginSuccessResponse {
    status: "SUCCESS";
    data: {
        user: UserInfo;
        token: TokenInfo;
    };
}

// 로그인 실패 응답 타입
export interface LoginErrorResponse {
    status: "FAIL";
    error: {
      code: string;
      message: string;
    };
  }

  // 로그인 응답 타입 (성공 또는 실패)
export type LoginResponse = LoginSuccessResponse | LoginErrorResponse;

const ERROR_MAPPING: Record<string, string> = {
    INVALID_CREDENTIALS: "아이디 또는 비밀번호가 올바르지 않습니다.",
};

/**
 * 로그인 API 호출
 * @param data 로그인 폼 데이터
 * @returns 로그인 결과
 */
export const Login = async (
    data: LoginRequest
): Promise<LoginResponse> => {
    try {
        // application/x-www-form-urlencoded 형식으로 데이터 변환
        const formData = new URLSearchParams();
        formData.append("username", data.username);
        formData.append("password", data.password);
        
        const response = await apiClient.post<LoginResponse>(
            "/auth/login",
            formData.toString(),
            {
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                withCredentials: true, // 쿠키를 주고받기 위한 필수 설정
            }
        );

        return response.data;
    } catch (error: unknown) {
        // HTTP 에러 응답 (4xx, 5xx)인 경우 에러 응답 반환
        const axiosError = error as AxiosErrorResponse & { response?: { data?: LoginResponse } };
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
    defaultMessage: string = "로그인에 실패했습니다."
): string => {
    if (!errorCode) return defaultMessage;

    return ERROR_MAPPING[errorCode] || defaultMessage;
};

