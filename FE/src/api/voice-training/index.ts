import { apiClient } from '@/api/axios';

export interface CreateVocalSessionRequest {
  session_name: string;
  type: 'vocal';
  item_count: number;
  training_date: string; // YYYY-MM-DD 형식
  session_metadata?: {
    training_types?: string[];
    [key: string]: any;
  };
}

export interface SubmitVocalItemRequest {
  sessionId: number;
  itemIndex: number;
  audioFile: File;
  graphImage: File;
  graphVideo?: File;
  onUploadProgress?: (progressEvent: any) => void;
}

export interface VocalSessionResponse {
  id: number;
  session_name: string;
  type: 'vocal';
  status: 'in_progress' | 'completed' | 'paused';
  total_items: number;
  completed_items: number;
  current_item_index: number;
  progress_percentage: number;
  training_items: Array<{
    id: number;
    item_index: number;
    is_completed: boolean;
    word_id: null;
    sentence_id: null;
  }>;
}

export interface VocalItemSubmissionResponse {
  session: VocalSessionResponse;
  next_item: {
    item_id: number;
    item_index: number;
    is_completed: boolean;
    has_next: boolean;
  } | null;
  media: {
    id: number;
    object_key: string;
    media_type: string;
  };
  praat: {
    pitch_mean?: number;
    pitch_std?: number;
    intensity_mean?: number;
    jitter?: number;
    shimmer?: number;
    [key: string]: any;
  } | null;
  video_url?: string;
  image_url?: string;
  video_image_url?: string;
}

/**
 * 발성 훈련 세션 생성
 */
export const createVocalSession = async (
  data: CreateVocalSessionRequest
): Promise<VocalSessionResponse> => {
  const response = await apiClient.post('/training-sessions', data);
  return response.data;
};

/**
 * 발성 훈련 아이템 제출
 */
export const submitVocalItem = async ({
  sessionId,
  itemIndex,
  audioFile,
  graphImage,
  graphVideo,
  onUploadProgress,
}: SubmitVocalItemRequest): Promise<VocalItemSubmissionResponse> => {
  const formData = new FormData();
  formData.append('audio_file', audioFile);
  formData.append('graph_image', graphImage);
  
  if (graphVideo) {
    formData.append('graph_video', graphVideo);
  }

  const response = await apiClient.post(
    `/training-sessions/${sessionId}/vocal/${itemIndex}/submit`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress,
    }
  );
  
  return response.data;
};

/**
 * 세션 완료 처리
 */
export const completeVocalSession = async (
  sessionId: number
): Promise<VocalSessionResponse> => {
  const response = await apiClient.post(`/training-sessions/${sessionId}/complete`);
  return response.data;
};

/**
 * 세션 조회
 */
export const getVocalSession = async (
  sessionId: number
): Promise<VocalSessionResponse> => {
  const response = await apiClient.get(`/training-sessions/${sessionId}`);
  return response.data;
};

/**
 * 현재 아이템 조회
 */
export const getCurrentVocalItem = async (sessionId: number) => {
  const response = await apiClient.get(`/training-sessions/${sessionId}/current-item`);
  return response.data;
};

/**
 * 특정 인덱스 아이템 조회
 */
export const getVocalItemByIndex = async (sessionId: number, itemIndex: number) => {
  const response = await apiClient.get(
    `/training-sessions/${sessionId}/items/index/${itemIndex}`
  );
  return response.data;
};

