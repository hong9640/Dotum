/**
 * 비디오 상태 타입 정의
 */

export interface VideoState {
  /** 사용자가 녹화한 비디오 URL */
  userVideoUrl?: string;
  /** Wav2Lip으로 합성된 비디오 URL */
  compositedVideoUrl?: string;
  /** 합성 비디오 로딩 중 여부 */
  isLoadingComposited: boolean;
  /** 합성 비디오 에러 메시지 */
  compositedVideoError: string | null;
}

/**
 * 초기 비디오 상태 생성
 */
export const createInitialVideoState = (): VideoState => ({
  userVideoUrl: undefined,
  compositedVideoUrl: undefined,
  isLoadingComposited: false,
  compositedVideoError: null,
});

