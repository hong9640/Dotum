import { useState, useEffect, type DependencyList } from 'react';

interface UseAsyncDataReturn<T> {
  data: T | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => void;
}

/**
 * 비동기 데이터 페칭 Hook
 * @param fetchFn - 데이터를 가져오는 비동기 함수
 * @param deps - 의존성 배열
 * @returns data, isLoading, error, refetch
 */
export function useAsyncData<T>(
  fetchFn: () => Promise<T>,
  deps: DependencyList = []
): UseAsyncDataReturn<T> {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const result = await fetchFn();
      setData(result);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '데이터를 불러오는데 실패했습니다.';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return {
    data,
    isLoading,
    error,
    refetch: loadData,
  };
}

