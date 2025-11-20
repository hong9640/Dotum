/**
 * 세션 완료 처리 관련 유틸리티
 */
import { getTrainingSession, completeTrainingSession } from "@/features/training-session/api";
import { toast } from "sonner";

export interface SessionCompletionOptions {
  sessionId: number;
  sessionIdParam: string;
  sessionTypeParam: string;
  onNavigate: (url: string) => void;
}

/**
 * 세션 완료 처리
 * 모든 아이템이 완료되었는지 확인 후 세션 완료 API 호출
 */
export const handleSessionCompletion = async (
  options: SessionCompletionOptions
): Promise<boolean> => {
  const { sessionId, sessionIdParam, sessionTypeParam, onNavigate } = options;

  try {
    // 먼저 세션 상태를 확인하여 모든 아이템이 완료되었는지 검증
    const sessionData = await getTrainingSession(sessionId);

    // total_items와 completed_items의 값이 같은지 확인
    if (sessionData.total_items !== sessionData.completed_items) {
      const trainingType = sessionData.type === 'word' ? '단어' : sessionData.type === 'sentence' ? '문장' : '발성';
      toast.error(`아직 제출하지 않은 ${trainingType} 연습이 있습니다.`);
      return false;
    }

    // 두 값이 같으면 세션 종료 API 호출
    await completeTrainingSession(sessionId);

    // 세션 종료 성공 후 result-list 페이지로 이동
    const resultListUrl = `/result-list?sessionId=${sessionIdParam}&type=${sessionTypeParam}`;
    onNavigate(resultListUrl);
    return true;
  } catch (error: unknown) {
    console.error('세션 완료 처리 실패:', error);

    const enhancedError = error as { status?: number; message?: string };
    
    if (enhancedError.status === 400) {
      const trainingType = sessionTypeParam === 'word' ? '단어' : sessionTypeParam === 'sentence' ? '문장' : '발성';
      toast.error(`아직 제출하지 않은 ${trainingType} 연습이 있습니다.`);
    } else if (enhancedError.status === 401) {
      toast.error('인증이 필요합니다. 다시 로그인해주세요.');
      onNavigate('/login');
    } else if (enhancedError.status === 404) {
      toast.error('세션을 찾을 수 없습니다. 홈페이지에서 다시 시작해주세요.');
      onNavigate('/');
    } else {
      const errorMessage = enhancedError.message || '세션 종료 중 오류가 발생했습니다.';
      toast.error(errorMessage);
    }
    
    return false;
  }
};

