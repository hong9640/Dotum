import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { 
  createWordTrainingSession, 
  createSentenceTrainingSession,
  getTrainingSessionErrorMessage,
  type CreateTrainingSessionResponse 
} from "@/api/training-session";

interface UseTrainingSessionProps {
  onSessionCreated?: (session: CreateTrainingSessionResponse) => void;
}

export const useTrainingSession = ({ onSessionCreated }: UseTrainingSessionProps = {}) => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  /**
   * 단어 훈련 세션 생성
   * @param itemCount 아이템 개수 (기본값: 10)
   * @param sessionName 세션 이름 (선택사항)
   */
  const createWordSession = async (itemCount: number = 10, sessionName?: string) => {
    setIsLoading(true);
    setApiError(null);

    try {
      const session = await createWordTrainingSession(itemCount, sessionName);
      
      toast.success("단어 훈련 세션이 생성되었습니다!");
      onSessionCreated?.(session);
      
      // 훈련 페이지로 이동 (세션 ID와 itemIndex를 쿼리 파라미터로 전달)
      navigate(`/practice?sessionId=${session.session_id}&type=word&itemIndex=0`);
      
      return session;
    } catch (error: any) {
      const errorMessage = error.response?.data?.error?.code 
        ? getTrainingSessionErrorMessage(error.response.data.error.code, error.response.data.error.message)
        : "네트워크 오류가 발생했습니다. 다시 시도해주세요.";
      
      setApiError(errorMessage);
      toast.error(errorMessage);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * 문장 훈련 세션 생성
   * @param itemCount 아이템 개수 (기본값: 5)
   * @param sessionName 세션 이름 (선택사항)
   */
  const createSentenceSession = async (itemCount: number = 5, sessionName?: string) => {
    setIsLoading(true);
    setApiError(null);

    try {
      const session = await createSentenceTrainingSession(itemCount, sessionName);
      
      toast.success("문장 훈련 세션이 생성되었습니다!");
      onSessionCreated?.(session);
      
      // 훈련 페이지로 이동 (세션 ID와 itemIndex를 쿼리 파라미터로 전달)
      navigate(`/practice?sessionId=${session.session_id}&type=sentence&itemIndex=0`);
      
      return session;
    } catch (error: any) {
      const errorMessage = error.response?.data?.error?.code 
        ? getTrainingSessionErrorMessage(error.response.data.error.code, error.response.data.error.message)
        : "네트워크 오류가 발생했습니다. 다시 시도해주세요.";
      
      setApiError(errorMessage);
      toast.error(errorMessage);
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
    clearError,
  };
};

export default useTrainingSession;
