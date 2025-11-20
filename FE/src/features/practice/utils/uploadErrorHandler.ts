/**
 * 업로드 에러 처리 유틸리티
 */
import { toast } from "sonner";

export interface UploadError {
  response?: {
    status?: number;
    data?: {
      detail?: string;
    };
  };
  message?: string;
}

export interface UploadErrorHandlerOptions {
  error: unknown;
  onNavigate: (url: string) => void;
  onRetake: () => void;
  onSetError: (error: string) => void;
}

/**
 * 업로드 에러 처리
 */
export const handleUploadError = (options: UploadErrorHandlerOptions): void => {
  const { error, onNavigate, onRetake, onSetError } = options;

  const axiosError = error as UploadError;
  const status = axiosError.response?.status;

  // 401: 인증 오류 - 강제 로그인 페이지 이동
  if (status === 401) {
    toast.error('세션이 만료되었습니다. 다시 로그인해주세요.');
    setTimeout(() => {
      onNavigate('/login');
    }, 1500);
    return;
  }

  // 404: 세션 없음 - 강제 홈으로 이동
  if (status === 404) {
    toast.error('세션을 찾을 수 없습니다. 홈에서 다시 시작해주세요.');
    setTimeout(() => {
      onNavigate('/');
    }, 1500);
    return;
  }

  // 422: 파일 오류 - 강제 다시 녹화
  if (status === 422) {
    toast.error('파일이 올바르지 않습니다. 다시 녹화해주세요.');
    onRetake();
    return;
  }

  // 그 외 에러 (네트워크, 서버 오류) - 재시도 가능
  let errorMessage = '영상 업로드에 실패했습니다.';
  if (axiosError.response?.data?.detail) {
    errorMessage = axiosError.response.data.detail;
  }

  onSetError(errorMessage);
};

