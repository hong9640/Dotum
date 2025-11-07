import { apiClient } from "../axios";

// Praat 분석 결과 타입 (나중에 확장될 수 있음)
export interface PraatResult {
  praat_id?: number;
  media_id?: number;
  jitter_local?: number;
  shimmer_local?: number;
  hnr?: number;
  nhr?: number;
  f0?: number;
  max_f0?: number;
  min_f0?: number;
  cpp?: number;
  csid?: number;
}

// 단일 아이템 상세 조회 응답 타입
export interface SessionItemResponse {
  item_id: number;
  item_index: number;
  word_id?: number | null;
  sentence_id?: number | null;
  word?: string | null;
  sentence?: string | null;
  is_completed?: boolean;
  video_url?: string | null;
  composited_video_url?: string | null;
  media_file_id?: number | null;
  composited_media_file_id?: number | null;
  has_next?: boolean;
  praat?: PraatResult | null;
}

// 에러 응답 타입
export interface SessionItemErrorResponse {
  detail: string;
}

// 통합 응답 타입
export type SessionItemApiResponse = SessionItemResponse | SessionItemErrorResponse;

/**
 * 단일 아이템 상세 조회 API 호출
 * @param sessionId 세션 ID
 * @param itemIndex 아이템 인덱스
 * @returns 단일 아이템 상세 정보
 */
export const getSessionItemByIndex = async (
  sessionId: number,
  itemIndex: number
): Promise<SessionItemResponse> => {
  console.log('📤 단일 아이템 상세 조회 요청:', { sessionId, itemIndex });
  
  const response = await apiClient.get<SessionItemResponse>(
    `/train/training-sessions/${sessionId}/items/index/${itemIndex}`,
    {
      headers: {
        "Accept": "application/json",
      },
    }
  );

  console.log('📥 단일 아이템 상세 조회 응답:', response.data);
  return response.data;
};

/**
 * API 에러 메시지를 사용자 친화적인 메시지로 변환
 * @param error API 에러 객체
 * @returns 사용자 친화적인 에러 메시지
 */
export const getSessionItemErrorMessage = (error: any): string => {
  if (error.response?.status === 401) {
    return "인증이 필요합니다. 다시 로그인해주세요.";
  }
  
  if (error.response?.status === 404) {
    return "세션이나 아이템을 찾을 수 없습니다.";
  }
  
  if (error.response?.status === 422) {
    return "요청 데이터가 올바르지 않습니다.";
  }
  
  if (error.response?.data?.detail) {
    return error.response.data.detail;
  }
  
  return "아이템 정보를 불러오는데 실패했습니다.";
};

