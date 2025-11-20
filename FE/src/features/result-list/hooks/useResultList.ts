import { useState, useEffect, useCallback } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { getSessionDetail } from "../api/session-detail-search";
import { retryTrainingSession } from "../../training-session/api/session-retry";
import { useTrainingSession } from "../../training-session/hooks";
import { useAlertDialog } from "@/shared/hooks/useAlertDialog";
import { formatDate } from "@/shared/utils/dateFormatter";
import type { WordResult } from "../types";
import type { VoiceMetrics } from "../types";
import {
  isVoiceTraining,
  transformToWordResults,
  extractVoiceMetrics,
  extractOverallFeedback,
} from "../utils/transformSessionDetail";

export interface UseResultListReturn {
  // 상태
  isLoading: boolean;
  error: string | null;
  resultsData: WordResult[];
  sessionType: 'word' | 'sentence' | 'vocal';
  formattedDate: string;
  totalItems: number;
  voiceMetrics: VoiceMetrics;
  isVoiceTraining: boolean;
  overallFeedback: string | null;
  isRetrying: boolean;
  isCreatingSession: boolean;

  // URL 파라미터
  sessionIdParam: string | null;
  typeParam: 'word' | 'sentence' | 'vocal' | null;
  dateParam: string | null;

  // 핸들러
  handleBack: () => void;
  handleDetailClick: (result: WordResult) => void;
  handleRetry: () => Promise<void>;
  handleNewTraining: () => Promise<void>;
  showAlert: (options: { description: string }) => void;
  AlertDialog: React.ComponentType;
}

/**
 * ResultListPage의 모든 비즈니스 로직을 관리하는 훅
 */
export const useResultList = (): UseResultListReturn => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // 상태
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [resultsData, setResultsData] = useState<WordResult[]>([]);
  const [sessionType, setSessionType] = useState<'word' | 'sentence' | 'vocal'>('word');
  const [formattedDate, setFormattedDate] = useState<string>('');
  const [totalItems, setTotalItems] = useState<number>(0);
  const [voiceMetrics, setVoiceMetrics] = useState<VoiceMetrics>({
    cpp: null,
    csid: null,
    jitter: null,
    shimmer: null,
    nhr: null,
    hnr: null,
    maxF0: null,
    minF0: null,
    lhRatioMeanDb: null,
    lhRatioSdDb: null,
  });
  const [isVoiceTrainingState, setIsVoiceTrainingState] = useState<boolean>(false);
  const [overallFeedback, setOverallFeedback] = useState<string | null>(null);
  const [isRetrying, setIsRetrying] = useState(false);

  // URL 파라미터
  const sessionIdParam = searchParams.get('sessionId');
  const typeParam = searchParams.get('type') as 'word' | 'sentence' | 'vocal' | null;
  const dateParam = searchParams.get('date');

  // 연습 세션 훅
  const { createWordSession, createSentenceSession, isLoading: isCreatingSession } = useTrainingSession();

  // AlertDialog 훅
  const { showAlert, AlertDialog: AlertDialogComponent } = useAlertDialog();

  // 페이지 진입 시 상단으로 스크롤
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [sessionIdParam, typeParam]);

  // 세션 상세 조회 API 호출
  useEffect(() => {
    const loadSessionDetail = async () => {
      if (!sessionIdParam || !typeParam) {
        setError('세션 정보가 없습니다. 홈페이지에서 다시 시작해주세요.');
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        setError(null);

        const sessionId = Number(sessionIdParam);
        if (isNaN(sessionId)) {
          setError('세션 ID가 유효하지 않습니다.');
          setIsLoading(false);
          return;
        }

        // API 호출
        const sessionDetailData = await getSessionDetail(sessionId);

        // 세션 타입 설정
        const sessionTypeLower = (sessionDetailData.type || '').toLowerCase();
        const finalSessionType = sessionTypeLower as 'word' | 'sentence' | 'vocal';
        setSessionType(finalSessionType);

        // total_items 저장
        setTotalItems(sessionDetailData.total_items || 0);

        // 날짜 포맷팅
        const formatted = formatDate(sessionDetailData.training_date);
        setFormattedDate(formatted);

        // 발성 연습 여부 확인
        const isVoice = isVoiceTraining(sessionDetailData.type, typeParam);
        setIsVoiceTrainingState(isVoice);

        // 데이터 변환
        const wordResults = transformToWordResults(sessionDetailData, isVoice);
        setResultsData(wordResults);

        const metrics = extractVoiceMetrics(sessionDetailData, isVoice);
        setVoiceMetrics(metrics);

        const feedback = extractOverallFeedback(sessionDetailData, isVoice);
        setOverallFeedback(feedback);

        setIsLoading(false);
      } catch (err: unknown) {
        console.error('세션 상세 조회 실패:', err);

        const enhancedError = err as { status?: number; message?: string };
        let errorMessage = '세션 상세 조회에 실패했습니다.';
        if (enhancedError.status === 401) {
          errorMessage = '인증이 필요합니다. 다시 로그인해주세요.';
        } else if (enhancedError.status === 404) {
          errorMessage = '세션을 찾을 수 없습니다.';
        }

        if (enhancedError.message) {
          errorMessage = enhancedError.message;
        }

        setError(errorMessage);
        setIsLoading(false);
      }
    };

    loadSessionDetail();
  }, [sessionIdParam, typeParam]);

  const handleBack = useCallback(() => {
    if (dateParam) {
      navigate(`/training-history?date=${dateParam}`);
    } else {
      navigate('/');
    }
  }, [navigate, dateParam]);

  const handleDetailClick = useCallback((result: WordResult) => {
    if (!sessionIdParam || !typeParam) {
      console.error('세션 정보가 없습니다.');
      showAlert({ description: '세션 정보를 찾을 수 없습니다.' });
      return;
    }

    // 발성 연습일 때는 praat-detail로 이동
    if (sessionType === 'vocal' || (typeParam && typeParam.toLowerCase() === 'vocal')) {
      const n = totalItems > 0 ? Math.floor(totalItems / 5) : 0;
      const trainingIndex = result.id - 1;
      const itemIndex = trainingIndex * n;

      let praatUrl = `/praat-detail?sessionId=${sessionIdParam}&itemIndex=${itemIndex}`;
      if (dateParam) {
        praatUrl += `&date=${dateParam}`;
      }
      navigate(praatUrl);
    } else {
      // 단어/문장 연습: result-detail 페이지로 이동
      let detailUrl = `/result-detail?sessionId=${sessionIdParam}&type=${typeParam}&itemIndex=${result.id - 1}`;
      if (dateParam) {
        detailUrl += `&date=${dateParam}`;
      }
      navigate(detailUrl);
    }
  }, [sessionIdParam, typeParam, sessionType, totalItems, dateParam, navigate, showAlert]);

  const handleRetry = useCallback(async () => {
    if (isRetrying) return;

    if (!sessionIdParam) {
      console.error('세션 ID가 없습니다.');
      showAlert({ description: '세션 정보를 찾을 수 없습니다.' });
      return;
    }

    try {
      setIsRetrying(true);

      const sessionId = Number(sessionIdParam);
      if (isNaN(sessionId)) {
        showAlert({ description: '유효하지 않은 세션 ID입니다.' });
        setIsRetrying(false);
        return;
      }

      const retrySession = await retryTrainingSession(sessionId);

      if (retrySession.session_id && retrySession.type) {
        navigate(`/practice?sessionId=${retrySession.session_id}&type=${retrySession.type}&itemIndex=0`);
      } else {
        showAlert({ description: '재연습 세션 정보가 올바르지 않습니다.' });
        setIsRetrying(false);
      }
    } catch (error: unknown) {
      console.error('재연습 세션 생성 실패:', error);
      const errorWithMessage = error as { message?: string };
      showAlert({ description: errorWithMessage.message || '재연습 세션 생성에 실패했습니다.' });
      setIsRetrying(false);
    }
  }, [sessionIdParam, isRetrying, navigate, showAlert]);

  const handleNewTraining = useCallback(async () => {
    try {
      if (sessionType === 'word') {
        await createWordSession(2);
      } else {
        await createSentenceSession(2);
      }
    } catch (error) {
      console.error('새로운 연습 세션 생성 실패:', error);
    }
  }, [sessionType, createWordSession, createSentenceSession]);

  return {
    isLoading,
    error,
    resultsData,
    sessionType,
    formattedDate,
    totalItems,
    voiceMetrics,
    isVoiceTraining: isVoiceTrainingState,
    overallFeedback,
    isRetrying,
    isCreatingSession,
    sessionIdParam,
    typeParam,
    dateParam,
    handleBack,
    handleDetailClick,
    handleRetry,
    handleNewTraining,
    showAlert,
    AlertDialog: AlertDialogComponent,
  };
};

