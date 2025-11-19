import { apiClient } from "@/shared/api/axios";
import { clearAuthCookies } from "@/shared/utils/cookies";
import type { AxiosErrorResponse } from "@/shared/types/api";

// 로그아웃 성공 응답 타입
export interface LogoutSuccessResponse {
    status: "SUCCESS";
    message: string;
}

// 로그아웃 실패 응답 타입
export interface LogoutErrorResponse {
    status: "FAIL";
    error: {
        code: string;
        message: string;
    };
}

// 로그아웃 응답 타입 (성공 또는 실패)
export type LogoutResponse = LogoutSuccessResponse | LogoutErrorResponse;

/**
 * 로그아웃 API 호출
 * @returns 로그아웃 결과
 */
export const Logout = async (): Promise<LogoutResponse> => {
    try {
        const response = await apiClient.post<LogoutResponse>("/auth/logout");
        
        // 로그아웃 성공 시 쿠키 정리
        if (response.data.status === "SUCCESS") {
            // 쿠키에서 access_token과 refresh_token 삭제
            clearAuthCookies();
            
        }
        
        return response.data;
    } catch (error: unknown) {
        console.error("❌ 로그아웃 API 에러:", error);
        const axiosError = error as AxiosErrorResponse & { response?: { data?: LogoutResponse } };
        
        // API 에러가 발생해도 클라이언트 측 정리는 수행
        clearAuthCookies();
        
        // 에러 응답 반환
        if (axiosError.response?.data) {
            return axiosError.response.data;
        }
        
        // 네트워크 에러 등 기타 에러
        return {
            status: "FAIL",
            error: {
                code: "NETWORK_ERROR",
                message: "네트워크 오류가 발생했습니다."
            }
        };
    }
};
