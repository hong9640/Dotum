import { apiClient } from "../axios";
import type { CreateTrainingSessionResponse } from "./index";

/**
 * 완료된 훈련 세션 재훈련 API 호출
 * @param sessionId 세션 ID
 * @returns 재훈련 세션 생성 결과
 * @throws {Error} API 호출 실패 시 에러 발생
 */
export const retryTrainingSession = async (
  sessionId: number
): Promise<CreateTrainingSessionResponse> => {
  console.log('📤 훈련 세션 재훈련 요청:', { sessionId });
  
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

    console.log('📥 훈련 세션 재훈련 응답:', response.data);
    return response.data;
  } catch (error: any) {
    console.error('❌ 훈련 세션 재훈련 API 에러:', {
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data,
      sessionId
    });

    // 에러 메시지 추출
    let errorMessage = '훈련 세션 재훈련에 실패했습니다.';
    
    if (error.response?.data?.detail) {
      if (Array.isArray(error.response.data.detail)) {
        // 422 Validation Error
        errorMessage = '요청 데이터가 올바르지 않습니다.';
      } else {
        errorMessage = error.response.data.detail;
      }
    } else if (error.response?.status === 400) {
      errorMessage = '완료되지 않은 세션이거나 잘못된 요청입니다.';
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

