import { apiClient } from "../axios";

// 현재 진행 중인 아이템 응답 타입
export interface CurrentItemResponse {
  id: number;
  item_index: number;
  word_id: number | null;
  sentence_id: number | null;
  word: string | null;
  sentence: string | null;
  is_completed: boolean;
  video_url: string | null;
  media_file_id: number | null;
  has_next: boolean;
}

// 에러 응답 타입
export interface CurrentItemErrorResponse {
  detail: string;
}

// 통합 응답 타입
export type CurrentItemApiResponse = CurrentItemResponse | CurrentItemErrorResponse;

/**
 * 현재 진행 중인 아이템 조회 API 호출
 * @param sessionId 세션 ID
 * @returns 현재 진행 중인 아이템 정보
 */
export const getCurrentItem = async (
  sessionId: number
): Promise<CurrentItemResponse> => {
  
  const response = await apiClient.get<CurrentItemResponse>(
    `/train/training-sessions/${sessionId}/current-item`,
    {
      headers: {
        "Accept": "application/json",
      },
    }
  );

  return response.data;
};

/**
 * API 에러 메시지를 사용자 친화적인 메시지로 변환
 * @param error API 에러 객체
 * @returns 사용자 친화적인 에러 메시지
 */
export const getCurrentItemErrorMessage = (error: unknown): string => {
  const axiosError = error as { response?: { status?: number } };
  if (axiosError.response?.status === 401) {
    return "인증이 필요합니다. 다시 로그인해주세요.";
  }
  
  if (axiosError.response?.status === 404) {
    return "세션을 찾을 수 없습니다.";
  }
  
  if (axiosError.response?.status === 422) {
    return "요청 데이터가 올바르지 않습니다.";
  }
  
  const axiosErrorWithDetail = error as { response?: { data?: { detail?: string } } };
  if (axiosErrorWithDetail.response?.data?.detail) {
    return axiosErrorWithDetail.response.data.detail;
  }
  
  return "현재 진행 중인 아이템을 불러오는데 실패했습니다.";
};
