import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { 
  createWordTrainingSession, 
  createSentenceTrainingSession,
  createVocalTrainingSession,
  type CreateTrainingSessionResponse 
} from "@/api/trainingSession";
import type { AxiosErrorResponse } from "@/types/api";

interface UseTrainingSessionProps {
  onSessionCreated?: (session: CreateTrainingSessionResponse) => void;
}

export const useTrainingSession = ({ onSessionCreated }: UseTrainingSessionProps = {}) => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  /**
   * 단어 연습 세션 생성
   * @param itemCount 아이템 개수 (기본값: 3)
   * @param sessionName 세션 이름 (선택사항)
   */
  const createWordSession = async (itemCount: number = 3, sessionName?: string) => {
    // 이미 로딩 중이면 중복 실행 방지
    if (isLoading) return;
    
    setIsLoading(true);
    setApiError(null);

    try {
      const session = await createWordTrainingSession(itemCount, sessionName);
      
      onSessionCreated?.(session);
      
      // 연습 페이지로 이동 (세션 ID와 itemIndex를 쿼리 파라미터로 전달)
      navigate(`/practice?sessionId=${session.session_id}&type=word&itemIndex=0`);
      
      return session;
    } catch (error: unknown) {
      // 401 에러 처리 - 로그인 필요
      const axiosError = error as AxiosErrorResponse;
      if (axiosError.response?.status === 401) {
        navigate('/login');
        return;
      }

      const errorMessage = axiosError.response?.data?.error?.message || 
                           axiosError.response?.data?.message || 
                           "";
      
      if (errorMessage) {
        setApiError(errorMessage);
        toast.error(errorMessage);
      }
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * 문장 연습 세션 생성
   * @param itemCount 아이템 개수 (기본값: 3)
   * @param sessionName 세션 이름 (선택사항)
   */
  const createSentenceSession = async (itemCount: number = 3, sessionName?: string) => {
    // 이미 로딩 중이면 중복 실행 방지
    if (isLoading) return;
    
    setIsLoading(true);
    setApiError(null);

    try {
      const session = await createSentenceTrainingSession(itemCount, sessionName);
      
      onSessionCreated?.(session);
      
      // 연습 페이지로 이동 (세션 ID와 itemIndex를 쿼리 파라미터로 전달)
      navigate(`/practice?sessionId=${session.session_id}&type=sentence&itemIndex=0`);
      
      return session;
    } catch (error: unknown) {
      // 401 에러 처리 - 로그인 필요
      const axiosError = error as AxiosErrorResponse;
      if (axiosError.response?.status === 401) {
        navigate('/login');
        return;
      }

      const errorMessage = axiosError.response?.data?.error?.message || 
                           axiosError.response?.data?.message || 
                           "";
      
      if (errorMessage) {
        setApiError(errorMessage);
        toast.error(errorMessage);
      }
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * 발성 연습 세션 생성
   * @param itemCount 아이템 개수 (기본값: 15)
   * @param sessionName 세션 이름 (선택사항)
   */
  const createVocalSession = async (itemCount: number = 15, sessionName?: string) => {
    // 이미 로딩 중이면 중복 실행 방지
    if (isLoading) return;
    
    setIsLoading(true);
    setApiError(null);

    try {
      const session = await createVocalTrainingSession(itemCount, sessionName);
      
      onSessionCreated?.(session);
      
      return session;
    } catch (error: unknown) {
      // 401 에러 처리 - 로그인 필요
      const axiosError = error as AxiosErrorResponse;
      if (axiosError.response?.status === 401) {
        navigate('/login');
        return;
      }

      const errorMessage = axiosError.response?.data?.error?.message || 
                           axiosError.response?.data?.message || 
                           "";
      
      if (errorMessage) {
        setApiError(errorMessage);
        toast.error(errorMessage);
      }
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * 에러 상태 초기화
   */
  const clearError = () => {
    setApiError(null);
  };

  return {
    // 상태
    isLoading,
    apiError,
    
    // 액션
    createWordSession,
    createSentenceSession,
    createVocalSession,
    clearError,
  };
};

export default useTrainingSession;
