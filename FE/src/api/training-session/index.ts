import { apiClient } from "../axios";

// 훈련 세션 타입 정의
export type TrainingType = 'word' | 'sentence' | 'vocal';

// 훈련 세션 생성 요청 타입
export interface CreateTrainingSessionRequest {
  session_name: string;
  type: TrainingType;
  item_count: number;
  training_date: string; // 'YYYY-MM-DD' 형식
  session_metadata?: Record<string, unknown>;
}

// 훈련 아이템 타입
export interface TrainingItem {
  item_id: number;
  training_session_id: number;
  item_index: number;
  word_id?: number | null;
  sentence_id?: number | null;
  word?: string | null; // 단어 텍스트
  sentence?: string | null; // 문장 텍스트
  feedback?: string | null; // 피드백
  score?: number | null; // 점수
  is_completed?: boolean;
  video_url?: string | null;
  composited_video_url?: string | null;
  media_file_id?: number | null;
  composited_media_file_id?: number | null;
  completed_at?: string | null;
  created_at?: string;
  updated_at?: string;
}

// 세션 Praat 분석 결과 타입
export interface SessionPraatResult {
  avg_jitter_local?: number | null;
  avg_shimmer_local?: number | null;
  avg_hnr?: number | null;
  avg_nhr?: number | null;
  avg_lh_ratio_mean_db?: number | null;
  avg_lh_ratio_sd_db?: number | null;
  avg_max_f0?: number | null;
  avg_min_f0?: number | null;
  avg_intensity_mean?: number | null;
  avg_f0?: number | null;
  avg_f1?: number | null;
  avg_f2?: number | null;
  avg_cpp?: number | null;
  avg_csid?: number | null;
  created_at?: string;
  updated_at?: string;
}

// 훈련 세션 생성 응답 타입
export interface CreateTrainingSessionResponse {
  session_id: number;
  user_id: number;
  session_name?: string;
  type: TrainingType;
  status: 'in_progress' | 'completed' | 'paused';
  training_date: string; // ISO8601 형식
  total_items?: number;
  completed_items?: number;
  current_item_index?: number;
  progress_percentage?: number;
  average_score?: number | null; // 전체 평균 점수
  overall_feedback?: string | null; // 전체 피드백
  session_praat_result?: SessionPraatResult | null; // Praat 분석 결과
  session_metadata?: Record<string, unknown>;
  created_at?: string;
  updated_at?: string;
  started_at?: string | null;
  completed_at?: string | null;
  training_items?: TrainingItem[];
}

// 에러 응답 타입
export interface TrainingSessionErrorResponse {
  status: "FAIL";
  error: {
    code: string;
    message: string;
  };
}

// 훈련 세션 완료 에러 응답 타입 (스웨거 스펙 기반)
export interface CompleteSessionErrorResponse {
  detail: string;
}

// Validation Error 응답 타입
export interface ValidationErrorResponse {
  detail: Array<{
    loc: string[];
    msg: string;
    type: string;
  }>;
}

// 성공 응답 타입
export interface TrainingSessionSuccessResponse {
  status: "SUCCESS";
  data: CreateTrainingSessionResponse;
}

// 통합 응답 타입
export type TrainingSessionResponse = TrainingSessionSuccessResponse | TrainingSessionErrorResponse;

// 에러 매핑 테이블
const ERROR_MAPPING: Record<string, string> = {
  INVALID_SESSION_TYPE: "유효하지 않은 세션 타입입니다.",
  INVALID_ITEM_COUNT: "아이템 개수는 1개 이상이어야 합니다.",
  INVALID_DATE_FORMAT: "날짜 형식이 올바르지 않습니다.",
  SESSION_LIMIT_EXCEEDED: "세션 생성 한도를 초과했습니다.",
  UNAUTHORIZED: "인증이 필요합니다.",
  FORBIDDEN: "접근 권한이 없습니다.",
};

/**
 * 훈련 세션 생성 API 호출
 * @param data 훈련 세션 생성 요청 데이터
 * @returns 훈련 세션 생성 결과
 */
export const createTrainingSession = async (
  data: CreateTrainingSessionRequest
): Promise<CreateTrainingSessionResponse> => {
  console.log('📤 훈련 세션 생성 요청 데이터:', data);
  
  const response = await apiClient.post<CreateTrainingSessionResponse>(
    "/train/training-sessions",
    data,
    {
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
      },
    }
  );

  return response.data;
};

/**
 * 단어 훈련 세션 생성 (편의 함수)
 * @param itemCount 아이템 개수
 * @param sessionName 세션 이름 (선택사항)
 * @returns 훈련 세션 생성 결과
 */
export const createWordTrainingSession = async (
  itemCount: number = 2,
  sessionName?: string
): Promise<CreateTrainingSessionResponse> => {
  const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD 형식
  
  return createTrainingSession({
    session_name: sessionName || `${today} 단어훈련`,
    type: 'word',
    item_count: itemCount,
    training_date: today,
    session_metadata: {
      level: 'basic',
      note: 'word training session'
    }
  });
};

/**
 * 문장 훈련 세션 생성 (편의 함수)
 * @param itemCount 아이템 개수
 * @param sessionName 세션 이름 (선택사항)
 * @returns 훈련 세션 생성 결과
 */
export const createSentenceTrainingSession = async (
  itemCount: number = 10,
  sessionName?: string
): Promise<CreateTrainingSessionResponse> => {
  const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD 형식
  
  return createTrainingSession({
    session_name: sessionName || `${today} 문장훈련`,
    type: 'sentence',
    item_count: itemCount,
    training_date: today,
    session_metadata: {
      level: 'basic',
      note: 'sentence training session'
    }
  });
};

/**
 * 발성 훈련 세션 생성 (편의 함수)
 * @param itemCount 아이템 개수
 * @param sessionName 세션 이름 (선택사항)
 * @returns 훈련 세션 생성 결과
 */
export const createVocalTrainingSession = async (
  itemCount: number = 15,
  sessionName?: string
): Promise<CreateTrainingSessionResponse> => {
  const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD 형식
  
  return createTrainingSession({
    session_name: sessionName || `${today} 발성훈련`,
    type: 'vocal',
    item_count: itemCount,
    training_date: today,
    session_metadata: {
      level: 'basic',
      note: 'vocal training session'
    }
  });
};

/**
 * 훈련 세션 조회 API 호출
 * @param sessionId 세션 ID
 * @returns 훈련 세션 정보
 */
export const getTrainingSession = async (
  sessionId: number
): Promise<CreateTrainingSessionResponse> => {
  console.log('📤 훈련 세션 조회 요청:', { sessionId });
  
  const response = await apiClient.get<CreateTrainingSessionResponse>(
    `/train/training-sessions/${sessionId}`,
    {
      headers: {
        "Accept": "application/json",
      },
    }
  );

  console.log('📥 훈련 세션 조회 응답:', response.data);
  return response.data;
};

/**
 * 훈련 세션 완료 API 호출
 * @param sessionId 세션 ID
 * @returns 완료된 훈련 세션 정보
 * @throws {Error} API 호출 실패 시 에러 발생
 */
export const completeTrainingSession = async (
  sessionId: number
): Promise<CreateTrainingSessionResponse> => {
  console.log('📤 훈련 세션 완료 요청:', { sessionId });
  
  try {
    const response = await apiClient.post<CreateTrainingSessionResponse>(
      `/train/training-sessions/${sessionId}/complete`,
      {}, // Body 없음
      {
        headers: {
          "Accept": "application/json",
        },
      }
    );

    console.log('📥 훈련 세션 완료 응답:', response.data);
    return response.data;
  } catch (error: any) {
    console.error('❌ 훈련 세션 완료 API 에러:', {
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data,
      sessionId
    });

    // 에러 메시지 추출
    let errorMessage = '훈련 세션 완료에 실패했습니다.';
    
    if (error.response?.data?.detail) {
      errorMessage = error.response.data.detail;
    } else if (error.response?.status === 400) {
      errorMessage = '아직 모든 아이템이 완료되지 않았습니다.';
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

/**
 * API 에러 코드를 사용자 친화적인 메시지로 변환
 * @param errorCode API 에러 코드
 * @param defaultMessage 기본 에러 메시지
 * @returns 사용자 친화적인 에러 메시지
 */
export const getTrainingSessionErrorMessage = (
  errorCode?: string,
  defaultMessage: string = "훈련 세션 생성에 실패했습니다."
): string => {
  if (!errorCode) return defaultMessage;
  
  return ERROR_MAPPING[errorCode] || defaultMessage;
};
