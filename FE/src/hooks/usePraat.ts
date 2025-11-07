import { useEffect, useMemo, useRef, useState } from "react";
import { fetchPraat } from "@/api/training-session/praat";
import type { PraatMetrics } from "@/api/training-session/praat";

export function usePraat(
  sessionId: number | undefined,
  itemId: number | undefined,
  options?: {
    token?: string;
    withCredentials?: boolean;
    pollIntervalMs?: number; // 예: 2500
    maxPollMs?: number;      // 예: 60000
    enabled?: boolean;
  }
) {
  const {
    token,
    withCredentials,
    pollIntervalMs = 2500,
    maxPollMs = 60000,
    enabled = true,
  } = options || {};

  const [data, setData] = useState<PraatMetrics | null>(null);
  const [loading, setLoading] = useState<boolean>(enabled);
  const [processing, setProcessing] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  const abortRef = useRef<AbortController | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const deadline = useMemo(
    () => Date.now() + maxPollMs,
    [maxPollMs, sessionId, itemId]
  );

  useEffect(() => {
    console.log("🔍 usePraat 체크:", { enabled, sessionId, itemId });
    
    if (!enabled || !sessionId || !itemId) {
      console.log("⏸️ usePraat 비활성화:", { enabled, sessionId, itemId });
      setLoading(false);
      setProcessing(false);
      setData(null);
      setError(null);
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
      if (abortRef.current) {
        abortRef.current.abort();
        abortRef.current = null;
      }
      return;
    }

    console.log("✅ usePraat 시작 - Praat API 호출:", { sessionId, itemId });

    // 기존 요청 및 타이머 정리
    abortRef.current?.abort();
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }

    abortRef.current = new AbortController();
    setLoading(true);
    setProcessing(false);
    setError(null);
    setData(null);

    const tick = async () => {
      try {
        console.log("📤 Praat API 호출:", { sessionId, itemId });
        const res = await fetchPraat(sessionId, itemId, {
          signal: abortRef.current?.signal,
          token,
          withCredentials,
        });

        console.log("📥 Praat API 응답:", res);

        if (res.status === "done") {
          console.log("✅ Praat 분석 완료:", res.data);
          setData(res.data);
          setProcessing(false);
          setLoading(false);
          return; // stop polling
        }

        // processing
        console.log("⏳ Praat 분석 처리 중...");
        setProcessing(true);
        setLoading(false);

        if (Date.now() >= deadline) {
          throw new Error(
            "분석 대기 시간이 초과되었습니다. 잠시 후 다시 시도해 주세요."
          );
        }

        console.log(`⏰ ${pollIntervalMs}ms 후 재시도 예약`);
        timerRef.current = setTimeout(tick, pollIntervalMs);
      } catch (e: any) {
        // 취소된 요청이면 무시
        if (e?.name === "CanceledError" || e?.message?.includes("cancel")) {
          console.log("🚫 Praat API 요청 취소됨");
          return;
        }

        console.error("❌ Praat API 에러:", e);
        setLoading(false);
        setProcessing(false);
        setError(e);
      }
    };

    tick();

    return () => {
      abortRef.current?.abort();
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [
    sessionId,
    itemId,
    token,
    withCredentials,
    pollIntervalMs,
    maxPollMs,
    enabled,
    deadline,
  ]);

  return { data, loading, processing, error };
}

