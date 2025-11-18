import { apiClient } from "../axios";

// Wav2Lip 결과 영상 URL 조회 성공 응답 타입
export interface CompositedVideoResponse {
  upload_url: string;
  media_file_id: number;
  expires_in: number;
}

// 영상 합성 중 응답 타입 (202)
export interface CompositedVideoProcessingResponse {
  detail: string;
}

// 에러 응답 타입
export interface CompositedVideoErrorResponse {
  detail: string | Array<{
    loc: (string | number)[];
    msg: string;
    type: string;
  }>;
}

/**
 * Wav2Lip 결과 영상 URL 조회 API 호출
 * @param sessionId 세션 ID
 * @param itemId 아이템 ID (item_index가 아님!)
 * @returns Wav2Lip 결과 영상 URL 정보
 * @throws {Error} 202 응답인 경우 에러로 처리하여 폴링 계속 진행
 */
export const getCompositedVideoUrl = async (
  sessionId: number,
  itemId: number
): Promise<CompositedVideoResponse> => {
  
  try {
    const response = await apiClient.get<CompositedVideoResponse | CompositedVideoProcessingResponse>(
      `/train/training-sessions/${sessionId}/items/${itemId}/result`,
      {
        headers: {
          "Accept": "application/json",
        },
        validateStatus: (status) => {
          // 200과 202 모두 성공으로 처리
          return status === 200 || status === 202;
        },
      }
    );

    // 200 응답인 경우
    if (response.status === 200) {
      return response.data as CompositedVideoResponse;
    }

    // 202 응답인 경우 에러로 처리하여 폴링 계속 진행
    if (response.status === 202) {
      throw {
        response: {
          status: 202,
          data: response.data as CompositedVideoProcessingResponse
        }
      };
    }

    // 예상치 못한 상태 코드
    throw {
      response: {
        status: response.status,
        data: response.data
      }
    };
  } catch (error: unknown) {
    // 이미 에러 형태로 처리한 경우 그대로 재throw
    const axiosError = error as { response?: { status?: number } };
    if (axiosError.response?.status === 202) {
      throw error;
    }
    // axios 에러인 경우 그대로 재throw
    throw error;
  }
};

/**
 * detail 필드를 안전하게 문자열로 변환
 */
const toErrorMessage = (detail: unknown): string | null => {
  if (!detail) return null;
  
  if (typeof detail === 'string') return detail;
  
  if (Array.isArray(detail)) {
    // FastAPI ValidationError 스타일
    return detail.map((e) => {
      const loc = Array.isArray(e?.loc) ? e.loc.join('.') : '';
      const msg = e?.msg ?? '오류';
      return loc ? `${loc}: ${msg}` : msg;
    }).join(' / ');
  }
  
  if (typeof detail === 'object') {
    const detailWithMessage = detail as { message?: string };
    return detailWithMessage.message || JSON.stringify(detail);
  }
  
  return String(detail);
};

/**
 * API 에러 메시지를 사용자 친화적인 메시지로 변환
 * @param error API 에러 객체
 * @returns 사용자 친화적인 에러 메시지
 */
export const getCompositedVideoErrorMessage = (error: unknown): string => {
  const axiosError = error as { response?: { status?: number; data?: { detail?: unknown } } };
  if (axiosError.response?.status === 401) {
    return "인증이 필요합니다. 다시 로그인해주세요.";
  }
  
  if (axiosError.response?.status === 404) {
    return "세션이나 아이템을 찾을 수 없습니다.";
  }
  
  if (axiosError.response?.status === 422) {
    return "요청 데이터가 올바르지 않습니다.";
  }
  
  const detail = axiosError.response?.data?.detail;
  const msg = toErrorMessage(detail);
  
  return msg || "Wav2Lip 결과 영상 URL을 불러오는데 실패했습니다.";
};

