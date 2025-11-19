# 내부 로직 개선 계획

## 📊 현재 상태 분석

구조 개선(Phase 1-3)이 완료되었으므로, 이제 **내부 로직 품질 개선**에 집중합니다.

## 🔴 우선순위 1 (Critical) - 즉시 개선 필요

### 1. `features/practice/pages/PracticePage.tsx` (718줄)

**문제점:**
- ⚠️ **파일이 너무 길다** (700줄 이상) - 유지보수 어려움
- ⚠️ **복잡한 상태 관리** - 10개 이상의 useState
- ⚠️ **중복된 로직** - 비디오 상태 설정 로직이 4곳에서 반복
- ⚠️ **깊은 중첩** - try-catch 중첩, 조건문 중첩
- ⚠️ **타이밍 이슈** - `setTimeout` 사용 (라인 329, 451, 461, 542, 600)
- ⚠️ **console.error 남용** - 9개 이상
- ⚠️ **복잡한 비동기 흐름** - handleUpload 내부에 200줄 이상의 로직

**개선 전략:**

#### 1-1. 커스텀 훅으로 분리

```
features/practice/hooks/
├── usePracticeSession.ts          # ✅ 이미 존재 (사용 안 함)
├── usePracticeVideoState.ts       # 🆕 비디오 상태 관리
├── usePracticeUpload.ts           # 🆕 업로드 로직 (useVideoUpload 활용)
└── usePracticeNavigation.ts       # ✅ 이미 존재 (사용 안 함)
```

**작업 내용:**
1. `usePracticeVideoState` 생성
   - 비디오 상태 초기화/업데이트 로직 통합
   - `updateVideoStateFromItem` 유틸 함수 포함
2. `usePracticeUpload` 생성
   - `useVideoUpload` 훅 활용
   - 업로드 후 다음 아이템 이동 로직 포함
3. `usePracticeSession` 활용
   - 현재 PracticePage에 직접 구현된 세션 로딩 로직을 이 훅으로 대체

#### 1-2. 유틸 함수 추출

```
features/practice/utils/
└── videoStateUtils.ts             # 🆕 비디오 상태 관련 유틸
```

**작업 내용:**
- `updateVideoStateFromItem(item: SessionItemResponse): VideoState` - 비디오 상태 설정 로직 통합
- `shouldStartPolling(item, videoState): boolean` - 폴링 조건 계산

#### 1-3. 에러 처리 통합

```
shared/utils/
└── errorHandler.ts                # 🆕 공통 에러 처리
```

**작업 내용:**
- `handleApiError(error: unknown, context: string): void` - 공통 에러 처리
- `getErrorMessage(error: unknown): string` - 에러 메시지 추출
- `handleAuthError(error: unknown, navigate: NavigateFunction): void` - 인증 에러 처리
- `handleSessionError(error: unknown, navigate: NavigateFunction): void` - 세션 에러 처리

#### 1-4. setTimeout 제거

- React 18의 자동 배칭 활용
- `flushSync` 사용 (필요시)
- URL 업데이트는 `useEffect`로 처리

**예상 작업 시간:** 6-8시간

---

### 2. `features/practice/components/result/ResultComponent.tsx`

**문제점:**
- ⚠️ **중복된 에러 처리** - PracticePage와 동일한 에러 처리 로직
- ⚠️ **console.error 사용** - 3개
- ⚠️ **타입 안정성** - `unknown as { status?: number }` 타입 단언

**개선 방안:**
1. 공통 에러 처리 유틸 함수 사용 (`shared/utils/errorHandler.ts`)
2. 타입 안전한 에러 처리 함수 구현
3. console.error 제거 또는 로깅 라이브러리로 대체

**예상 작업 시간:** 1-2시간

---

## 🟡 우선순위 2 (High) - 단기 개선 필요

### 3. `features/training-session/hooks/index.ts` (useTrainingSession)

**문제점:**
- ⚠️ **중복된 에러 처리** - 3개 함수에서 동일한 패턴 반복
- ⚠️ **에러 메시지 파싱 로직 중복**

**개선 방안:**
1. 공통 에러 처리 함수 추출 (`shared/utils/errorHandler.ts` 사용)
2. 에러 메시지 파싱 유틸 함수 생성

**예상 작업 시간:** 1시간

---

### 4. `features/result-list/pages/ResultListPage.tsx` (442줄)

**문제점:**
- ⚠️ **복잡한 데이터 변환 로직** - 발성 연습/일반 연습 분기
- ⚠️ **많은 useState** - 9개
- ⚠️ **console.error 사용** - 5개
- ⚠️ **긴 useEffect** - 100줄 이상

**개선 방안:**

#### 4-1. 데이터 변환 로직 분리

```
features/result-list/utils/
└── dataTransformers.ts            # 🆕 데이터 변환 유틸
```

**작업 내용:**
- `transformSessionDetailToWordResults(sessionDetail, isVoice): WordResult[]` - 세션 상세를 WordResult 배열로 변환
- `transformVocalTrainingToWordResults(sessionDetail): WordResult[]` - 발성 연습 전용 변환
- `transformRegularTrainingToWordResults(sessionDetail): WordResult[]` - 일반 연습 전용 변환

#### 4-2. 커스텀 훅으로 분리

```
features/result-list/hooks/
└── useResultListData.ts           # 🆕 결과 목록 데이터 관리
```

**작업 내용:**
- 세션 상세 조회
- 데이터 변환
- 상태 관리 (resultsData, voiceMetrics, overallFeedback 등)

**예상 작업 시간:** 2-3시간

---

### 5. `features/result-detail/pages/ResultDetailPage.tsx`

**문제점:**
- ⚠️ **복잡한 useEffect** - 여러 관심사가 섞여 있음
- ⚠️ **타입 안정성** - `unknown as` 타입 단언
- ⚠️ **console.error 사용**

**개선 방안:**
1. 데이터 로딩 로직을 커스텀 훅으로 분리: `useResultDetailData`
2. 타입 안전한 에러 처리

**예상 작업 시간:** 1-2시간

---

## 🟢 우선순위 3 (Medium) - 중기 개선 필요

### 6. 사용되지 않는 훅 정리

**문제점:**
- `usePracticeSession.ts` - PracticePage에서 직접 구현되어 사용 안 함
- `useVideoUpload.ts` - PracticePage에서 직접 구현되어 사용 안 함
- `usePracticeNavigation.ts` - 사용 안 함

**개선 방안:**
1. PracticePage에서 이 훅들을 사용하도록 리팩토링
2. 또는 사용되지 않으면 삭제

**예상 작업 시간:** 2-3시간

---

### 7. 전역 에러 처리 및 로깅 개선

**문제점:**
- ⚠️ **console.error 남용** - 65개 이상
- ⚠️ **일관성 없는 에러 처리**

**개선 방안:**

#### 7-1. 로깅 유틸 함수 생성

```
shared/utils/
└── logger.ts                      # 🆕 로깅 유틸
```

**작업 내용:**
- `logError(error: unknown, context: string): void` - 에러 로깅
- `logWarning(message: string, context?: string): void` - 경고 로깅
- `logInfo(message: string, context?: string): void` - 정보 로깅
- 개발 환경에서만 console 사용, 프로덕션에서는 에러 모니터링 서비스 연동 (선택)

#### 7-2. 에러 바운더리 추가

```
shared/components/error/
└── ErrorBoundary.tsx              # 🆕 에러 바운더리
```

**예상 작업 시간:** 2-3시간

---

### 8. 타입 안정성 개선

**문제점:**
- ⚠️ **타입 단언 남용** - `unknown as { status?: number }` 등

**개선 방안:**

#### 8-1. 타입 가드 함수 생성

```
shared/utils/
└── typeGuards.ts                  # 🆕 타입 가드
```

**작업 내용:**
- `isAxiosError(error: unknown): error is AxiosError`
- `hasStatus(error: unknown, status: number): boolean`
- `hasMessage(error: unknown): error is { message: string }`

**예상 작업 시간:** 1-2시간

---

## 📋 개선 로드맵

### Phase 1: Critical Issues (1주)

**목표:** PracticePage.tsx 리팩토링 및 공통 유틸 함수 생성

1. **Day 1-2: 공통 유틸 함수 생성**
   - `shared/utils/errorHandler.ts` 생성
   - `shared/utils/logger.ts` 생성
   - `shared/utils/typeGuards.ts` 생성

2. **Day 3-4: PracticePage 훅 분리**
   - `usePracticeVideoState.ts` 생성
   - `usePracticeUpload.ts` 생성 (useVideoUpload 활용)
   - `usePracticeSession.ts` 활용

3. **Day 5: PracticePage 리팩토링**
   - 훅들을 사용하도록 PracticePage 수정
   - setTimeout 제거
   - 에러 처리 통합

4. **Day 6-7: 테스트 및 버그 수정**
   - 타입 체크
   - 빌드 테스트
   - 주요 플로우 수동 테스트

---

### Phase 2: High Priority (1주)

**목표:** 나머지 페이지 및 훅 개선

1. **Day 1: ResultComponent 개선**
   - 공통 에러 처리 적용
   - console.error 제거

2. **Day 2: useTrainingSession 개선**
   - 중복 에러 처리 제거

3. **Day 3-4: ResultListPage 리팩토링**
   - 데이터 변환 로직 분리
   - `useResultListData` 훅 생성

4. **Day 5: ResultDetailPage 개선**
   - `useResultDetailData` 훅 생성

5. **Day 6-7: 테스트 및 버그 수정**

---

### Phase 3: Medium Priority (1주)

**목표:** 사용되지 않는 코드 정리 및 전역 개선

1. **Day 1-2: 사용되지 않는 훅 정리**
   - PracticePage에서 훅 사용하도록 리팩토링
   - 또는 삭제

2. **Day 3-4: 전역 로깅 시스템 구축**
   - logger.ts 완성
   - console.error 전역 교체

3. **Day 5: 에러 바운더리 추가**
   - ErrorBoundary 컴포넌트 생성
   - App.tsx에 적용

4. **Day 6-7: 타입 안정성 개선**
   - 타입 가드 함수 적용
   - 타입 단언 최소화

---

## 🎯 개선 원칙

1. **단일 책임 원칙** - 각 함수/훅은 하나의 책임만
2. **DRY (Don't Repeat Yourself)** - 중복 코드 제거
3. **컴포지션** - 작은 훅/함수 조합
4. **타입 안정성** - unknown as 최소화, 타입 가드 활용
5. **에러 처리 일관성** - 공통 에러 처리 패턴
6. **테스트 가능성** - 순수 함수로 분리
7. **점진적 개선** - 한 번에 모든 것을 바꾸지 않음

---

## 📊 통계 요약

### 파일별 복잡도
| 파일 | 줄 수 | useState | useEffect | console.error | setTimeout | 우선순위 |
|------|-------|----------|-----------|---------------|------------|----------|
| PracticePage.tsx | 718 | 10+ | 5+ | 9 | 5 | 🔴 1 |
| ResultListPage.tsx | 442 | 9 | 2 | 5 | 0 | 🟡 4 |
| ResultComponent.tsx | 169 | 1 | 0 | 3 | 0 | 🔴 2 |
| useTrainingSession.ts | 168 | 2 | 0 | 0 | 0 | 🟡 3 |
| ResultDetailPage.tsx | 243 | 7 | 3 | 1 | 0 | 🟡 5 |

### 주요 문제점 카테고리
1. **코드 중복** - 에러 처리, 비디오 상태 설정
2. **긴 파일** - PracticePage.tsx (718줄)
3. **복잡한 상태 관리** - 많은 useState
4. **타이밍 이슈** - setTimeout 사용 (42곳)
5. **로깅** - console.error 남용 (65개 이상)
6. **타입 안정성** - unknown as 타입 단언

---

## ✅ 체크리스트

각 Phase가 끝날 때마다 다음을 확인:

- [ ] `tsc --noEmit` 기준 타입 에러가 없는지
- [ ] 앱이 빌드/실행되는지
- [ ] 다음 주요 플로우가 정상 동작하는지:
  - [ ] 연습 진행 → 결과 보기 (practice)
  - [ ] 결과 상세 페이지 (result-detail)
  - [ ] 결과 목록 페이지 (result-list)
  - [ ] voice-training에서 StatusBadge 표시
  - [ ] Praat 상세 페이지에서 StatusBadge 표시

