# Utils vs Hooks 역할 기준

## 📋 기본 원칙

**React 의존 여부**를 기준으로 구분합니다.

- **`utils/`**: React 없이도 사용 가능한 순수 로직
- **`hooks/`**: React 상태/라이프사이클/이펙트가 필요한 로직

## ✅ Utils (`src/utils/`)

### 특징
- React에 의존하지 않음
- 순수 함수 (Pure Functions)
- 재사용 가능한 유틸리티 함수
- 테스트하기 쉬움

### 예시

#### ✅ 올바른 Utils
```typescript
// utils/cn.ts - 클래스명 병합
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// utils/dateFormatter.ts - 날짜 포맷팅
export const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return `${date.getFullYear()}년 ${date.getMonth() + 1}월 ${date.getDate()}일`;
};

// utils/cookies.ts - 쿠키 조작
export const getCookie = (name: string): string | null => {
  // document.cookie 사용하지만 React 의존 없음
  const nameEQ = name + "=";
  const ca = document.cookie.split(';');
  // ...
};

// utils/tts.ts - TTS 중지
export const stopAllTTS = (): void => {
  if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
    window.speechSynthesis.cancel();
  }
};

// utils/result-list/utils.ts - 데이터 변환
export const convertSessionsToTrainingSets = (
  response: DailyRecordSearchResponse
): TrainingSet[] => {
  // 순수 데이터 변환 로직
  return sessions.map((session) => ({ ... }));
};
```

### Utils에 포함되는 것들
- 문자열/숫자/날짜 포맷팅
- 데이터 변환/매핑
- 유효성 검사
- 쿠키/로컬스토리지 조작
- URL 파싱/생성
- 배열/객체 조작 헬퍼
- 순수 계산 함수

## ✅ Hooks (`src/hooks/`)

### 특징
- React Hooks 사용 (useState, useEffect, useCallback, useRef 등)
- 컴포넌트 상태 관리
- 라이프사이클 관리
- 사이드 이펙트 처리
- 컴포넌트에서만 사용 가능

### 예시

#### ✅ 올바른 Hooks
```typescript
// hooks/shared/useTTS.ts - TTS 상태 관리
export const useTTS = (options: UseTTSOptions = {}): UseTTSReturn => {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isSupported, setIsSupported] = useState(false);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  useEffect(() => {
    // Web Speech API 지원 여부 확인
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      setIsSupported(true);
    }
    return () => {
      // 클린업
      if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const speak = useCallback((text: string) => {
    // 상태 업데이트 포함
    setIsSpeaking(true);
    // ...
  }, [isSupported, lang, rate, pitch, volume]);

  return { speak, stop, isSpeaking, isSupported };
};

// hooks/shared/useAsyncData.ts - 비동기 데이터 페칭
export function useAsyncData<T>(
  fetchFn: () => Promise<T>,
  deps: DependencyList = []
): UseAsyncDataReturn<T> {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // 비동기 데이터 로딩
    loadData();
  }, deps);

  return { data, isLoading, error, refetch: loadData };
};

// hooks/shared/useMediaQuery.ts - 미디어 쿼리 상태
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    const media = window.matchMedia(query);
    setMatches(media.matches);

    const listener = () => {
      setMatches(media.matches);
    };

    media.addEventListener('change', listener);
    return () => media.removeEventListener('change', listener);
  }, [matches, query]);

  return matches;
}
```

### Hooks에 포함되는 것들
- 상태 관리 (useState)
- 라이프사이클 관리 (useEffect)
- 이벤트 리스너 관리
- 폴링/인터벌 관리
- API 호출 및 상태 관리
- 브라우저 API와의 상호작용 (상태 필요 시)

## 🔄 분리 전략

### TTS 예시 (잘 분리된 케이스)

#### Utils: 순수 함수
```typescript
// utils/tts.ts
export const stopAllTTS = (): void => {
  if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
    window.speechSynthesis.cancel();
  }
};
```

#### Hooks: 상태 관리
```typescript
// hooks/shared/useTTS.ts
import { stopAllTTS } from '@/utils/tts';

export const useTTS = (options: UseTTSOptions = {}): UseTTSReturn => {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isSupported, setIsSupported] = useState(false);
  
  // 상태 관리 로직...
  
  const stop = useCallback(() => {
    stopAllTTS(); // utils 함수 사용
    setIsSpeaking(false);
  }, [isSupported]);

  return { speak, stop, isSpeaking, isSupported };
};
```

## ❌ 잘못된 예시

### ❌ Utils에 React 의존성 포함
```typescript
// ❌ 잘못됨 - React Hook 사용
export const useFormatDate = (dateString: string) => {
  const [formatted, setFormatted] = useState('');
  useEffect(() => {
    setFormatted(formatDate(dateString));
  }, [dateString]);
  return formatted;
};

// ✅ 올바름 - 순수 함수
export const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return `${date.getFullYear()}년 ${date.getMonth() + 1}월`;
};
```

### ❌ Hooks에 순수 로직 포함
```typescript
// ❌ 잘못됨 - React 없이도 동작 가능
export const useFormatDate = (dateString: string) => {
  const date = new Date(dateString);
  return `${date.getFullYear()}년 ${date.getMonth() + 1}월`;
};

// ✅ 올바름 - utils로 이동
export const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return `${date.getFullYear()}년 ${date.getMonth() + 1}월`;
};
```

## 📁 현재 구조

### Utils (`src/utils/`)
- ✅ `cn.ts` - 클래스명 병합
- ✅ `cookies.ts` - 쿠키 조작
- ✅ `dateFormatter.ts` - 날짜 포맷팅
- ✅ `tts.ts` - TTS 중지 함수
- ✅ `result-list/utils.ts` - 데이터 변환
- ✅ `training-history-detail/utils.ts` - 데이터 변환

### Hooks (`src/hooks/shared/`)
- ✅ `useTTS.ts` - TTS 상태 관리 (utils/tts.ts 사용)
- ✅ `useAsyncData.ts` - 비동기 데이터 페칭
- ✅ `useMediaQuery.ts` - 미디어 쿼리 상태
- ✅ `useAlertDialog.tsx` - 다이얼로그 상태 관리

## 🎯 체크리스트

새로운 함수를 추가할 때:

- [ ] React Hook (useState, useEffect 등)을 사용하나?
  - ✅ Yes → `hooks/`
  - ❌ No → 다음 질문
- [ ] 컴포넌트 상태나 라이프사이클이 필요한가?
  - ✅ Yes → `hooks/`
  - ❌ No → `utils/`
- [ ] 순수 함수로 작성 가능한가?
  - ✅ Yes → `utils/`
  - ❌ No → `hooks/`

## 📝 참고

- Utils는 가능한 한 순수 함수로 작성
- Hooks는 Utils 함수를 내부에서 사용 가능
- Utils는 테스트하기 쉬워야 함
- Hooks는 컴포넌트에서만 사용 가능

