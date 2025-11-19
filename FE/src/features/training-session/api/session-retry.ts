import { apiClient } from "@/shared/api/axios";
import type { AxiosErrorResponse } from "@/shared/types/api";
import { EnhancedError } from "@/shared/types/api";
import type { CreateTrainingSessionResponse } from "./index";

/**
 * 완료된 연습 세션 재연습 API 호출
 * @param sessionId 세션 ID
 * @returns 재연습 세션 생성 결과
 * @throws {Error} API 호출 실패 시 에러 발생
 */
export const retryTrainingSession = async (
  sessionId: number
): Promise<CreateTrainingSessionResponse> => {
  
  try {
    const response = await apiClient.post<CreateTrainingSessionResponse>(
      `/train/training-sessions/${sessionId}/retry`,
      {}, // Body 없음 (session_name은 선택사항이고 현재로서는 보낼 필요 없음)
      {
        headers: {
          "Accept": "application/json",
        },
      }
    );

    return response.data;
  } catch (error: unknown) {
    const axiosError = error as AxiosErrorResponse;
    console.error('❌ 연습 세션 재연습 API 에러:', {
      status: axiosError.response?.status,
      statusText: axiosError.response?.statusText,
      data: axiosError.response?.data,
      sessionId
    });

    // 에러 메시지 추출
    let errorMessage = '연습 세션 재연습에 실패했습니다.';
    
    const detail = axiosError.response?.data?.detail;
    if (detail) {
      if (Array.isArray(detail)) {
        // 422 Validation Error
        errorMessage = '요청 데이터가 올바르지 않습니다.';
      } else {
        errorMessage = detail as string;
      }
    } else if (axiosError.response?.status === 400) {
      errorMessage = '완료되지 않은 세션이거나 잘못된 요청입니다.';
    } else if (axiosError.response?.status === 401) {
      errorMessage = '인증이 필요합니다. 다시 로그인해주세요.';
    } else if (axiosError.response?.status === 404) {
      errorMessage = '세션을 찾을 수 없습니다.';
    } else if (axiosError.response?.status === 422) {
      errorMessage = '요청 데이터가 올바르지 않습니다.';
    }

    // 에러 객체에 사용자 친화적인 메시지 추가
    throw new EnhancedError(errorMessage, axiosError.response?.status, error);
  }
};

