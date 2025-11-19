import { apiClient } from "@/shared/api/axios";
import type { SessionItemResponse } from "@/features/training-session/api/session-item-search";
import type { CreateTrainingSessionResponse } from "@/features/training-session/api";

// 제출 실패 응답 타입 (FastAPI 기본 ValidationError 형태 대응)
export interface ValidationError {
  detail: Array<{
    loc: (string | number)[];
    msg: string;
    type: string;
  }>;
}

// 업로드된 미디어 응답 타입
export interface MediaResponse {
  id: number;
  user_id: number;
  object_key: string;
  media_type?: "audio" | "video";
  file_name?: string;
  file_size_bytes?: number;
  format?: string;
  duration_ms?: number;
  width_px?: number;
  height_px?: number;
  status: "uploading" | "processing" | "completed" | "failed";
  is_public?: boolean;
  created_at?: string;
  updated_at?: string;
}

// 제출 성공 응답 타입
export interface SubmitCurrentItemResponse {
  session: CreateTrainingSessionResponse;
  next_item: SessionItemResponse | null;
  media: MediaResponse;
  video_url: string | null;
  message: string;
}

/**
 * 현재 진행 중인 아이템을 영상 파일로 제출하고 다음 아이템 정보를 반환합니다.
 * POST /api/v1/train/training-sessions/{session_id}/submit-current-item
 * Content-Type: multipart/form-data (file)
 */
export const submitCurrentItem = async (
  sessionId: number,
  file: File
): Promise<SubmitCurrentItemResponse> => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await apiClient.post<SubmitCurrentItemResponse>(
    `/train/training-sessions/${sessionId}/submit-current-item`,
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
        "Accept": "application/json",
      },
    }
  );

  return response.data;
};


