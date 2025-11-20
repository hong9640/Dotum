import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { getDailyRecordSearch } from "../api/daily-record-search";
import { completeTrainingSession } from "../../training-session/api";
import { convertSessionsToTrainingSets } from "../utils";
import { useTrainingDayDetail } from "./useTrainingDayDetail";
import { calculateTrainingSetPath } from "../utils/trainingSetNavigation";
import { formatDateForUrl } from "../utils/calendar";
import { toast } from "sonner";
import type { TrainingSet } from "../types";

export interface UseTrainingHistoryDetailOptions {
  date: string;
  trainingSets?: TrainingSet[];
}

export interface UseTrainingHistoryDetailReturn {
  // 상태
  actualTrainingSets: TrainingSet[];
  isLoading: boolean;
  error: string | null;
  totalSessions: number;
  isCompleting: boolean;
  statistics: {
    totalSets: number;
    totalWords: number;
  };

  // 핸들러
  handleTrainingSetClick: (trainingSet: TrainingSet) => Promise<void>;
}

/**
 * TrainingHistoryDetailPage의 모든 비즈니스 로직을 관리하는 훅
 */
export const useTrainingHistoryDetail = (
  options: UseTrainingHistoryDetailOptions
): UseTrainingHistoryDetailReturn => {
  const { date, trainingSets: propsTrainingSets } = options;
  const navigate = useNavigate();

  const [actualTrainingSets, setActualTrainingSets] = useState<TrainingSet[]>(
    propsTrainingSets || []
  );
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [totalSessions, setTotalSessions] = useState<number>(0);
  const [isCompleting, setIsCompleting] = useState(false);

  const { statistics } = useTrainingDayDetail({ trainingSets: actualTrainingSets });

  // API 호출
  useEffect(() => {
    // props로 trainingSets가 전달된 경우 API 호출하지 않음
    if (propsTrainingSets !== undefined) {
      setActualTrainingSets(propsTrainingSets);
      return;
    }

    // date가 없으면 처리하지 않음
    if (!date) {
      return;
    }

    const fetchDailyRecords = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await getDailyRecordSearch(date);

        // API 응답을 TrainingSet 배열로 변환
        const convertedSets = convertSessionsToTrainingSets(response);
        setActualTrainingSets(convertedSets);
        setTotalSessions(response.total_sessions);
      } catch (err: unknown) {
        console.error("일별 연습 기록 조회 실패 :", err);
        const axiosError = err as { response?: { data?: { detail?: string } } };
        setError(
          axiosError.response?.data?.detail || "연습 기록을 불러오는데 실패했습니다."
        );
        // 에러 발생 시 빈 배열 또는 더미 데이터 사용
        setActualTrainingSets([]);
        setTotalSessions(0);
      } finally {
        setIsLoading(false);
      }
    };

    fetchDailyRecords();
  }, [date, propsTrainingSets]);

  const handleTrainingSetClick = useCallback(
    async (trainingSet: TrainingSet) => {
      // 이미 세션 완료 처리 중이면 중복 실행 방지
      if (isCompleting) return;

      // 세션이 완료되지 않은 경우
      if (trainingSet.status !== "completed") {
        // 총 아이템 수와 완료된 아이템 수가 같은 경우 (실제로는 완료되었지만 status가 in_progress인 경우)
        if (
          trainingSet.completedItems !== undefined &&
          trainingSet.totalItems === trainingSet.completedItems
        ) {
          try {
            setIsCompleting(true);

            // 세션 종료 API 호출
            await completeTrainingSession(trainingSet.sessionId);

            // result-list 페이지로 이동
            const dateParam = formatDateForUrl(date);
            navigate(
              `/result-list?sessionId=${trainingSet.sessionId}&type=${trainingSet.type}&date=${dateParam}`
            );
          } catch (error: unknown) {
            console.error("세션 종료 실패:", error);
            const errorWithMessage = error as { message?: string };
            toast.error(
              errorWithMessage.message || "세션을 종료하는데 실패했습니다."
            );
            setIsCompleting(false);
          }
          return;
        }

        // 총 아이템 수와 완료된 아이템 수가 다른 경우 (실제로 진행 중인 경우)
        const message =
          "아직 연습이 완료되지 않았습니다.\n연습을 이어서 진행할까요? 😊";
        const shouldNavigate = window.confirm(message);

        if (shouldNavigate) {
          const path = calculateTrainingSetPath(trainingSet, date);
          if (path) {
            navigate(path);
          }
        }
        return;
      }

      // 완료된 세션은 result-list 페이지로 이동
      const dateParam = formatDateForUrl(date);
      navigate(
        `/result-list?sessionId=${trainingSet.sessionId}&type=${trainingSet.type}&date=${dateParam}`
      );
    },
    [date, navigate, isCompleting]
  );

  return {
    actualTrainingSets,
    isLoading,
    error,
    totalSessions,
    isCompleting,
    statistics,
    handleTrainingSetClick,
  };
};

