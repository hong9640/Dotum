import type React from 'react';

/**
 * 미디어 관련 공통 타입 정의
 */

export interface VideoPlayerCardProps {
  title: string;
  icon: React.ReactNode;
  videoSrc?: string;
  dialogContent: React.ReactNode;
  flipHorizontal?: boolean;
  isLoading?: boolean;
  errorMessage?: string;
}

export interface LargeVideoPlayerProps {
  title: string;
  icon: React.ReactNode;
  videoSrc?: string;
  posterSrc?: string;
  flipHorizontal?: boolean;
}

export interface ResultVideoDisplayProps {
  userVideoUrl?: string;
  compositedVideoUrl?: string;
  isLoadingCompositedVideo?: boolean;
  compositedVideoError?: string | null;
}

