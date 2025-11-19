import { apiClient } from "@/shared/api/axios";

/**
 * Praat 분석 결과 타입
 */
export interface PraatMetrics {
  id: number;
  media_id: number;
  // 음성 주파수/기초주파수
  f0: number;        // Hz
  max_f0: number;    // Hz
  min_f0: number;    // Hz
  // 음성 품질/잡음 관련
  jitter_local: number;   // %
  shimmer_local: number;  // dB 또는 %
  hnr: number;            // dB
  nhr: number;            // 비율(0~1) 또는 %
  cpp: number;            // dB
  csid: number;           // 단위 없음(지수형 스코어)
  // 발성 패턴(성문 좌/우 타격 비율 추정)
  lh_ratio_mean_db: number; // dB
  lh_ratio_sd_db: number;   // dB
  // 포먼트/강도
  f1: number;              // Hz
  f2: number;              // Hz
  intensity_mean: number;  // dB
}

export type PraatStatus = "done" | "processing";

export interface PraatOk {
  status: "done";
  data: PraatMetrics;
}

export interface PraatProcessing {
  status: "processing";
}

export type PraatResult = PraatOk | PraatProcessing;

/**
 * Praat 분석 결과 조회 API 호출
 * @param sessionId 세션 ID
 * @param itemId 아이템 ID
 * @param opts 옵션 (signal, token, withCredentials)
 * @returns Praat 분석 결과 또는 처리 중 상태
 */
export async function fetchPraat(
  sessionId: number,
  itemId: number,
  opts?: { signal?: AbortSignal; token?: string; withCredentials?: boolean }
): Promise<PraatResult> {
  const url = `/train/training-sessions/${sessionId}/items/${itemId}/praat`;
  
  const headers: Record<string, string> = { Accept: "application/json" };
  if (opts?.token) {
    headers.Authorization = `Bearer ${opts.token}`;
  }

  try {
    const response = await apiClient.get<PraatMetrics>(url, {
      headers,
      signal: opts?.signal,
      withCredentials: opts?.withCredentials !== undefined ? opts.withCredentials : true,
      validateStatus: (status) => status === 200 || status === 202, // 200과 202만 성공으로 처리
    });

    // 202 Accepted: 분석 처리 중
    if (response.status === 202) {
      return { status: "processing" };
    }

    // 200 OK: 분석 완료
    const data = response.data;
    return { status: "done", data };
  } catch (error: unknown) {
    // 표준화된 에러 throw: 상위에서 코드별 UI 처리
    const axiosError = error as { response?: { status?: number, data?: { detail?: string } }, message?: string };
    const status = axiosError.response?.status;
    const text = axiosError.response?.data?.detail || axiosError.message || "";
    const err = new Error(`Praat fetch failed: ${status} ${text}`);
    // @ts-expect-error - Error 객체에 커스텀 status 프로퍼티를 추가하기 위해 필요
    err.status = status;
    throw err;
  }
}

/**
 * API 에러 메시지를 사용자 친화적인 메시지로 변환
 * @param error API 에러 객체
 * @returns 사용자 친화적인 에러 메시지
 */
export const getPraatErrorMessage = (error: unknown): string => {
  const axiosError = error as { status?: number; response?: { status?: number; data?: { detail?: string } } };
  const status = axiosError?.status || axiosError?.response?.status;

  if (status === 403) {
    return "권한이 없습니다. 다시 로그인해 주세요.";
  }

  if (status === 404) {
    return "원본 미디어를 찾을 수 없습니다.";
  }

  if (status === 422) {
    return "잘못된 요청입니다. 세션/아이템 ID를 확인하세요.";
  }

  if (axiosError?.response?.data?.detail) {
    return axiosError.response.data.detail;
  }

  return "Praat 분석 결과를 불러오는데 실패했습니다.";
};

