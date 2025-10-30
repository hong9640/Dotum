import { apiClient } from "../axios";
import { clearAuthCookies } from "@/lib/cookies";

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
        
        // 로그아웃 성공 시 로컬 스토리지와 쿠키 정리
        if (response.data.status === "SUCCESS") {
            // 로컬 스토리지의 auth를 false로 설정
            localStorage.setItem("auth", "false");
            
            // 쿠키에서 access_token과 refresh_token 삭제
            clearAuthCookies();
            
            console.log("✅ 로그아웃 성공: 로컬 스토리지와 쿠키가 정리되었습니다.");
        }
        
        return response.data;
    } catch (error: any) {
        console.error("❌ 로그아웃 API 에러:", error);
        
        // API 에러가 발생해도 클라이언트 측 정리는 수행
        localStorage.setItem("auth", "false");
        clearAuthCookies();
        
        // 에러 응답 반환
        if (error.response?.data) {
            return error.response.data;
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
