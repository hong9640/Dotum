import { useEffect, useRef, useState } from "react";
import { getCompositedVideoUrl, getCompositedVideoErrorMessage } from "@/api/trainingSession/compositedVideoSearch";
import axios from "axios";

interface UseCompositedVideoPollingOptions {
  enabled: boolean;         // 폴링 시작 조건
  maxTries?: number;        // 기본 10
  baseIntervalMs?: number;  // 기본 10_000
  backoff?: boolean;        // 지수 백오프 적용 여부 (기본 false)
}

/**
 * Wav2Lip 결과 영상 URL 폴링 훅
 * @param sessionId 세션 ID
 * @param itemId 아이템 ID
 * @param options 폴링 옵션
 * @returns { url, loading, error } 폴링 결과
 */
export function useCompositedVideoPolling(
  sessionId: number | undefined,
  itemId: number | undefined,
  options: UseCompositedVideoPollingOptions = { enabled: false }
) {
  const {
    enabled,
    maxTries = 10,
    baseIntervalMs = 10_000,
    backoff = false,
  } = options;

  const [url, setUrl] = useState<string | undefined>(undefined);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const triesRef = useRef(0);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const busyRef = useRef(false);
  const abortRef = useRef<AbortController | null>(null);

  // 전역 클린업 (컴포넌트 언마운트 시)
  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current); // 예약된 타이머 취소
        timerRef.current = null; 
      }
      triesRef.current = 0; // 시도 횟수 초기화
      busyRef.current = false; // 폴링 중 상태 초기화
      if (abortRef.current) { // 진행 중 요청 취소
        abortRef.current.abort();
        abortRef.current = null;
      }
    };
  }, []); // 컴포넌트 언마운트 시 정리

  // 폴링 로직
  useEffect(() => {
    // 조건 불충족 시 정리
    if (!enabled || !sessionId || !itemId) {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
      triesRef.current = 0;
      busyRef.current = false;
      setLoading(false);
      if (abortRef.current) {
        abortRef.current.abort();
        abortRef.current = null;
      }
      return;
    }

    // 이미 폴링 중이면 중복 시작 방지
    if (busyRef.current) {
      return;
    }

    setLoading(true);
    setError(null);
    setUrl(undefined);
    triesRef.current = 0;
    busyRef.current = true;

    const doPoll = async () => {
      // 이전 요청 취소
      if (abortRef.current) {
        abortRef.current.abort(); // 이전 요청이 완료 전에 새 요청이 시작되면 이전 것을 취소
        // 현재는 signal 없어서 취소 기능 없음, 코드는 유지
      }

      // 새 요청 취소기 생성
      abortRef.current = new AbortController();

      try {
        triesRef.current += 1;

        const response = await getCompositedVideoUrl(
          sessionId,
          itemId
        );

        // 200 성공
        setUrl(response.upload_url);
        setError(null);
        setLoading(false);
        busyRef.current = false;

        if (timerRef.current) {
          clearTimeout(timerRef.current);
          timerRef.current = null;
        }
        if (abortRef.current) {
          abortRef.current = null;
        }
      } catch (e: unknown) {
        // 취소된 요청이면 종료
        const error = e as { name?: string, message?: string, response?: { status?: number } };
        if (axios.isCancel(e) || error?.name === 'CanceledError' || error?.message?.includes('cancel')) {
          return;
        }

        // 202: 계속 폴링
        if (error?.response?.status === 202) {

          if (triesRef.current >= maxTries) {
            setLoading(false);
            setError('합성된 동영상을 가져오는데 실패했습니다.');
            console.error('❌ Wav2Lip 결과 영상 URL 폴링 최대 시도 횟수 도달');
            busyRef.current = false;

            if (timerRef.current) {
              clearTimeout(timerRef.current);
              timerRef.current = null;
            }
            return;
          }

          // 백오프 계산 (backoff가 true인 경우) 
          // 폴링 실패 시 대기 간격을 점진적으로 증가, 현재는 고정 간격 사용
          let nextInterval = baseIntervalMs;
          if (backoff) {
            const factor = Math.pow(1.4, triesRef.current - 1); // 지수 백오프
            const jitter = Math.floor(Math.random() * 1200); // 0~1.2초 지터
            nextInterval = Math.min(60_000, Math.floor(baseIntervalMs * factor) + jitter);
          }

          timerRef.current = setTimeout(() => {
            doPoll();
          }, nextInterval);
        } else {
          // 기타 에러
          setLoading(false);
          const errorMessage = getCompositedVideoErrorMessage(error);
          setError(errorMessage);
          console.error('❌ Wav2Lip 결과 영상 URL 조회 실패:', errorMessage);
          busyRef.current = false;

          if (timerRef.current) {
            clearTimeout(timerRef.current);
            timerRef.current = null;
          }
        }
      }
    };

    // 즉시 1회 실행
    doPoll();

    // 의존성 변경 시 기존 타이머/요청 정리
    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
      if (abortRef.current) {
        abortRef.current.abort();
        abortRef.current = null;
      }
      triesRef.current = 0;
      busyRef.current = false;
    };
  }, [sessionId, itemId, enabled, maxTries, baseIntervalMs, backoff]);

  return { url, loading, error };
}

