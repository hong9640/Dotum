/**
 * 업로드 상태 타입 정의
 */

export interface UploadState {
  /** 업로드 진행 중 여부 */
  isUploading: boolean;
  /** 업로드 에러 메시지 */
  error: string | null;
  /** 녹화된 파일 */
  file: File | null;
}

/**
 * 초기 업로드 상태 생성
 */
export const createInitialUploadState = (): UploadState => ({
  isUploading: false,
  error: null,
  file: null,
});

