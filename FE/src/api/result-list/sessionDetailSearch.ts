import { apiClient } from "../axios";
import type { CreateTrainingSessionResponse, TrainingItem } from "../training-session";

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
  console.log('📤 훈련 세션 상세 조회 요청:', { sessionId });
  
  try {
    const response = await apiClient.get<SessionDetailResponse>(
      `/train/training-sessions/${sessionId}`,
      {
        headers: {
          "Accept": "application/json",
        },
      }
    );

    console.log('📥 훈련 세션 상세 조회 응답:', response.data);
    return response.data;
  } catch (error: any) {
    console.error('❌ 훈련 세션 상세 조회 API 에러:', {
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data,
      sessionId
    });

    // 에러 메시지 추출
    let errorMessage = '훈련 세션 상세 조회에 실패했습니다.';
    
    if (error.response?.data?.detail) {
      if (Array.isArray(error.response.data.detail)) {
        // 422 Validation Error
        errorMessage = '요청 데이터가 올바르지 않습니다.';
      } else {
        errorMessage = error.response.data.detail;
      }
    } else if (error.response?.status === 401) {
      errorMessage = '인증이 필요합니다. 다시 로그인해주세요.';
    } else if (error.response?.status === 404) {
      errorMessage = '세션을 찾을 수 없습니다.';
    } else if (error.response?.status === 422) {
      errorMessage = '요청 데이터가 올바르지 않습니다.';
    }

    // 에러 객체에 사용자 친화적인 메시지 추가
    const enhancedError = new Error(errorMessage);
    (enhancedError as any).status = error.response?.status;
    (enhancedError as any).originalError = error;
    
    throw enhancedError;
  }
};

