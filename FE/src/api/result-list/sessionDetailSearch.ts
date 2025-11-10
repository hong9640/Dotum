import { apiClient } from "../axios";
import type { CreateTrainingSessionResponse, TrainingItem } from "../training-session";
import type { AxiosErrorResponse } from "@/types/api";
import { EnhancedError } from "@/types/api";

/**
 * 훈련 세션 상세 조회 API 응답 타입
 * (기존 CreateTrainingSessionResponse와 동일한 구조이지만, 
 * training_items가 포함되어 있다는 점을 명확히 하기 위해 별도 타입 정의)
 */
export interface SessionDetailResponse extends CreateTrainingSessionResponse {
  training_items: TrainingItem[];
}

/**
 * 훈련 세션 상세 조회 API 호출
 * @param sessionId 세션 ID
 * @returns 훈련 세션 상세 정보 (training_items 포함)
 * @throws {Error} API 호출 실패 시 에러 발생
 */
export const getSessionDetail = async (
  sessionId: number
): Promise<SessionDetailResponse> => {
  
  try {
    const response = await apiClient.get<SessionDetailResponse>(
      `/train/training-sessions/${sessionId}`,
      {
        headers: {
          "Accept": "application/json",
        },
      }
    );

    return response.data;
  } catch (error: unknown) {
    const axiosError = error as AxiosErrorResponse;
    console.error('❌ 훈련 세션 상세 조회 API 에러:', {
      status: axiosError.response?.status,
      statusText: axiosError.response?.statusText,
      data: axiosError.response?.data,
      sessionId
    });

    // 에러 메시지 추출
    let errorMessage = '훈련 세션 상세 조회에 실패했습니다.';
    
    const detail = axiosError.response?.data?.detail;
    if (detail) {
      if (Array.isArray(detail)) {
        // 422 Validation Error
        errorMessage = '요청 데이터가 올바르지 않습니다.';
      } else {
        errorMessage = detail as string;
      }
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

