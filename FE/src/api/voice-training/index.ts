import { apiClient } from '@/api/axios';

// ============================================
// Vocal 전용 아이템 제출 API
// 세션 생성/조회/완료는 @/api/training-session 사용
// ============================================

export interface SubmitVocalItemRequest {
  sessionId: number;
  itemIndex: number;
  audioFile: File;
  graphImage: File;
  graphVideo?: File;
  onUploadProgress?: (progressEvent: any) => void;
}

export interface VocalItemSubmissionResponse {
  session: any;
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
 * 발성 훈련 아이템 제출 (오디오 + 그래프 이미지 업로드)
 * @param sessionId 세션 ID
 * @param itemIndex 아이템 인덱스
 * @param audioFile 오디오 파일 (WAV)
 * @param graphImage 그래프 이미지 파일
 * @param graphVideo 그래프 영상 파일 (선택사항)
 * @param onUploadProgress 업로드 진행률 콜백
 * @returns 제출 결과 및 다음 아이템 정보
 */
export const submitVocalItem = async ({
  sessionId,
  itemIndex,
  audioFile,
  graphImage,
  graphVideo,
  onUploadProgress,
}: SubmitVocalItemRequest): Promise<VocalItemSubmissionResponse> => {
  console.log('📤 발성 훈련 아이템 제출:', { sessionId, itemIndex });
  console.log('🎵 오디오 파일 정보:', {
    name: audioFile.name,
    type: audioFile.type,
    size: `${(audioFile.size / 1024).toFixed(2)} KB`
  });

  const formData = new FormData();
  formData.append('audio_file', audioFile);
  formData.append('graph_image', graphImage);
  
  if (graphVideo) {
    formData.append('graph_video', graphVideo);
  }

  const response = await apiClient.post(
    `/train/training-sessions/${sessionId}/vocal/${itemIndex}/submit`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress,
    }
  );
  
  console.log('📥 발성 훈련 아이템 제출 응답:', response.data);
  
  // 🔍 Praat 데이터 확인
  if (response.data.praat) {
    console.log('✅ Praat 데이터 있음:', response.data.praat);
  } else {
    console.warn('⚠️ Praat 데이터 없음 (null)');
  }
  
  return response.data;
};
