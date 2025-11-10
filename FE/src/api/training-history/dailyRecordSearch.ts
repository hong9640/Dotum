import { apiClient } from "../axios";

/**
 * 훈련 아이템 응답 타입
 */
export interface TrainingItemResponse {
  item_id: number;
  training_session_id?: number | null;
  item_index: number;
  word_id: number | null;
  word?: string | null;
  sentence_id: number | null;
  sentence?: string | null;
  is_completed: boolean;
  video_url?: string | null;
  media_file_id?: number | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * 세션 메타데이터 타입
 */
export interface SessionMetadata {
  [key: string]: unknown;
}

/**
 * 훈련 세션 응답 타입
 */
export interface TrainingSessionResponse {
  session_id: number;
  user_id: number;
  session_name?: string | null;
  type: 'word' | 'sentence';
  status: 'completed' | 'in_progress';
  training_date: string;
  total_items: number;
  completed_items: number;
  current_item_index: number;
  progress_percentage: number;
  average_score?: number | null; // 세션의 평균 점수 (completed일 때만 존재, 향후 백엔드 추가 예정)
  session_metadata: SessionMetadata;
  created_at: string;
  updated_at: string;
  started_at: string;
  completed_at: string | null;
  training_items: TrainingItemResponse[];
}

/**
 * 일별 훈련 기록 조회 응답 타입
 */
export interface DailyRecordSearchResponse {
  date: string;
  sessions: TrainingSessionResponse[];
  total_sessions: number;
  completed_sessions: number;
  in_progress_sessions: number;
}

/**
 * 일별 훈련 기록 조회
 * GET /train/training-sessions/daily/{date_str}
 *
 * @param dateStr - 날짜 문자열 (YYYY-MM-DD 형식)
 * @param type - 선택적 필터 타입 (word 또는 sentence)
 * @returns 일별 훈련 기록 응답
 */
export async function getDailyRecordSearch(
  dateStr: string,
  type?: 'word' | 'sentence'
): Promise<DailyRecordSearchResponse> {
  let url = `/train/training-sessions/daily/${dateStr}`;
  
  // type 파라미터가 있는 경우 쿼리 파라미터로 추가
  if (type) {
    url += `?type=${type}`;
  }
  
  const response = await apiClient.get<DailyRecordSearchResponse>(url);
  return response.data;
}

