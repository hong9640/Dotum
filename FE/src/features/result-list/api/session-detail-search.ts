
import { apiClient } from "@/shared/api/axios";
import type { TrainingItem } from "@/features/training-session/api";
import type { AxiosErrorResponse } from "@/shared/types/api";
import { EnhancedError } from "@/shared/types/api";

/**
 * 연습 세션 상세 조회 API 응답 타입
 */
export interface SessionDetailResponse {
  session_id: number;
  user_id: number;
  type: string;
  status: string;
  total_items: number;
  completed_items: number;
  training_date: string;
  created_at: string;
  updated_at: string;
  training_items: TrainingItem[];
  session_praat_result?: {
    avg_cpp?: number | null;
    avg_csid?: number | null;
    avg_jitter_local?: number | null;
    avg_shimmer_local?: number | null;
    avg_nhr?: number | null;
    avg_hnr?: number | null;
    avg_max_f0?: number | null;
    avg_min_f0?: number | null;
    avg_lh_ratio_mean_db?: number | null;
    avg_lh_ratio_sd_db?: number | null;
  } | null;
  overall_feedback?: string | null;
}

/**
 * 연습 세션 상세 조회 API 호출
 * @param sessionId 세션 ID
 * @returns 연습 세션 상세 정보 (training_items 포함)
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
    console.error('❌ 연습 세션 상세 조회 API 에러:', {
      status: axiosError.response?.status,
      statusText: axiosError.response?.statusText,
      data: axiosError.response?.data,
      sessionId
    });

    // 에러 메시지 추출
    let errorMessage = '연습 세션 상세 조회에 실패했습니다.';
    
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

