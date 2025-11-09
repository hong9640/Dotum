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
    if (!enabled || !sessionId || !itemId) {
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
        const res = await fetchPraat(sessionId, itemId, {
          signal: abortRef.current?.signal,
          token,
          withCredentials,
        });

        if (res.status === "done") {
          setData(res.data);
          setProcessing(false);
          setLoading(false);
          return;
        }

        setProcessing(true);
        setLoading(false);

        if (Date.now() >= deadline) {
          throw new Error(
            "분석 대기 시간이 초과되었습니다. 잠시 후 다시 시도해 주세요."
          );
        }

        timerRef.current = setTimeout(tick, pollIntervalMs);
      } catch (e: any) {
        if (e?.name === "CanceledError" || e?.message?.includes("cancel")) {
          return;
        }

        console.error("Praat API 오류:", e);
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

