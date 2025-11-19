import { apiClient } from "@/shared/api/axios";
import type { SessionItemResponse } from "@/features/training-session/api/session-item-search";
import type { CreateTrainingSessionResponse } from "@/features/training-session/api";
import type { MediaResponse } from "./index";
import type { PraatMetrics } from "@/features/training-session/api/praat";

// 재업로드 성공 응답 타입
export interface VideoReuploadResponse {
  session: CreateTrainingSessionResponse;
  next_item?: SessionItemResponse | null;
  media: MediaResponse;
  praat?: PraatMetrics | null;
  video_url?: string;
  message: string;
}

/**
 * 연습 아이템 동영상을 재업로드합니다.
 * PUT /api/v1/train/training-sessions/{session_id}/items/{item_id}/video
 * Content-Type: multipart/form-data (file)
 */
export const reuploadVideo = async (
  sessionId: number,
  itemId: number,
  file: File
): Promise<VideoReuploadResponse> => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await apiClient.put<VideoReuploadResponse>(
    `/train/training-sessions/${sessionId}/items/${itemId}/video`,
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

