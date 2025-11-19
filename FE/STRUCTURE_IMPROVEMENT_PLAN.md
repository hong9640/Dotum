# 폴더 구조 개선안 계획

## 📁 현재 아키텍처 트리 구조

```
src/
├── features/
│   ├── auth/
│   │   ├── api/
│   │   │   ├── login.ts
│   │   │   ├── logout.ts
│   │   │   ├── signup.ts
│   │   │   └── user.ts
│   │   ├── hooks/
│   │   │   ├── useLogin.ts
│   │   │   └── useSignup.ts
│   │   └── pages/
│   │       ├── login/
│   │       │   ├── components/
│   │       │   │   ├── ApiErrorDisplay.tsx
│   │       │   │   ├── LoginFooter.tsx
│   │       │   │   └── LoginForm.tsx
│   │       │   └── LoginPage.tsx
│   │       └── signup/
│   │           ├── components/
│   │           │   ├── EmailVerificationField.tsx
│   │           │   ├── FormField.tsx
│   │           │   └── SignupForm.tsx
│   │           └── SignupPage.tsx
│   │
│   ├── home/
│   │   └── pages/
│   │       └── HomePage.tsx
│   │
│   ├── practice/                    # 단어/문장 연습
│   │   ├── api/
│   │   │   ├── index.ts
│   │   │   └── video-reupload.ts
│   │   ├── components/
│   │   │   ├── practice/
│   │   │   │   ├── PracticeComponent.tsx
│   │   │   │   ├── RecordingControls.tsx
│   │   │   │   ├── RecordingPreview.tsx
│   │   │   │   ├── RecordingResult.tsx
│   │   │   │   └── RecordingTips.tsx
│   │   │   ├── result/              # ⚠️ 중복: result-detail과 공통 컴포넌트
│   │   │   │   ├── ActionButtons.tsx
│   │   │   │   ├── DetailedEvaluationItemCard.tsx
│   │   │   │   ├── DetailedEvaluationItems.tsx
│   │   │   │   ├── FeedbackCard.tsx
│   │   │   │   ├── FeedbackSummary.tsx
│   │   │   │   ├── ImprovementPoints.tsx
│   │   │   │   ├── LargeVideoPlayer.tsx
│   │   │   │   ├── PronunciationScore.tsx
│   │   │   │   ├── ResultComponent.tsx
│   │   │   │   ├── ResultVideoDisplay.tsx
│   │   │   │   └── VideoPlayerCard.tsx
│   │   │   └── TrainingLayout.tsx
│   │   ├── hooks/
│   │   │   ├── index.ts
│   │   │   ├── useCompositedVideoPolling.ts
│   │   │   ├── useMediaRecorder.ts
│   │   │   ├── usePracticeNavigation.ts
│   │   │   ├── usePracticeSession.ts
│   │   │   └── useVideoUpload.ts
│   │   ├── pages/
│   │   │   └── PracticePage.tsx
│   │   └── types/
│   │       ├── index.ts
│   │       ├── uploadState.ts
│   │       └── videoState.ts
│   │
│   ├── result-detail/               # 결과 상세 페이지
│   │   ├── components/
│   │   │   ├── evaluation/          # ⚠️ 중복: practice와 공통 컴포넌트
│   │   │   │   ├── DetailedEvaluationItemCard.tsx
│   │   │   │   └── DetailedEvaluationItems.tsx
│   │   │   ├── feedback/            # ⚠️ 중복: practice와 공통 컴포넌트
│   │   │   │   ├── FeedbackCard.tsx
│   │   │   │   ├── FeedbackSummary.tsx
│   │   │   │   ├── ImprovementPoints.tsx
│   │   │   │   └── PronunciationScore.tsx
│   │   │   ├── video/               # ⚠️ 중복: practice와 공통 컴포넌트
│   │   │   │   ├── LargeVideoPlayer.tsx
│   │   │   │   ├── ResultVideoDisplay.tsx
│   │   │   │   └── VideoPlayerCard.tsx
│   │   │   └── index.ts
│   │   ├── pages/
│   │   │   └── ResultDetailPage.tsx
│   │   └── utils/
│   │       ├── parseFeedback.ts
│   │       └── parseItemFeedback.ts
│   │
│   ├── result-list/                 # 결과 목록 페이지
│   │   ├── api/
│   │   │   └── session-detail-search.ts
│   │   ├── components/
│   │   │   ├── ActionButtons.tsx
│   │   │   ├── AverageScoreCard.tsx
│   │   │   ├── MetricCard.tsx
│   │   │   ├── WordResultItem.tsx
│   │   │   └── WordResultsList.tsx
│   │   ├── mockups/
│   │   │   ├── result-detail-mockup.tsx
│   │   │   └── result-list-mockup.tsx
│   │   ├── pages/
│   │   │   └── ResultListPage.tsx
│   │   ├── types/
│   │   │   ├── index.ts
│   │   │   ├── types.ts
│   │   │   └── voiceMetrics.ts
│   │   └── utils/
│   │       ├── diagnosePraat.ts
│   │       ├── index.ts
│   │       └── utils.ts
│   │
│   ├── training-history/            # 연습 기록
│   │   ├── api/
│   │   │   ├── daily-record-search.ts
│   │   │   └── index.ts
│   │   ├── components/
│   │   │   ├── Calendar.tsx
│   │   │   ├── CalendarGrid.tsx
│   │   │   ├── CalendarHeader.tsx
│   │   │   ├── CalendarLegend.tsx
│   │   │   ├── detail/
│   │   │   │   ├── EmptyState.tsx
│   │   │   │   ├── Header.tsx
│   │   │   │   ├── ScoreChip.tsx
│   │   │   │   ├── TrainingSetCard.tsx
│   │   │   │   ├── TrainingSetGrid.tsx
│   │   │   │   └── WordChip.tsx
│   │   │   └── index.ts
│   │   ├── hooks/
│   │   │   ├── index.ts
│   │   │   ├── useCalendar.ts
│   │   │   └── useTrainingDayDetail.ts
│   │   ├── pages/
│   │   │   ├── TrainingHistoryDetailPage.tsx
│   │   │   └── TrainingHistoryPage.tsx
│   │   ├── types/
│   │   │   ├── index.ts
│   │   │   └── types.ts
│   │   └── utils/
│   │       ├── index.ts
│   │       └── utils.ts
│   │
│   ├── training-session/            # 세션 관리 (API)
│   │   ├── api/
│   │   │   ├── composited-video-search.ts
│   │   │   ├── current-item.ts
│   │   │   ├── index.ts
│   │   │   ├── praat.ts
│   │   │   ├── session-item-search.ts
│   │   │   └── session-retry.ts
│   │   └── hooks/
│   │       └── index.ts
│   │
│   ├── voice-training/              # 발성 연습
│   │   ├── api/
│   │   │   └── index.ts
│   │   ├── components/
│   │   │   ├── AudioLevelGraph.tsx
│   │   │   ├── AudioPlayer.tsx
│   │   │   ├── PromptCardCrescendo.tsx
│   │   │   ├── PromptCardDecrescendo.tsx
│   │   │   ├── PromptCardLoudSoft.tsx
│   │   │   ├── PromptCardMPT.tsx
│   │   │   ├── PromptCardSoftLoud.tsx
│   │   │   ├── RecordToggle.tsx
│   │   │   ├── StatusBadge.tsx      # ⚠️ 중복: praat-detail과 공통 컴포넌트
│   │   │   └── WaveRecorder.tsx
│   │   ├── hooks/
│   │   │   ├── index.ts
│   │   │   └── useAudioRecorder.ts
│   │   ├── crescendo.tsx            # ⚠️ pages 폴더 없음
│   │   ├── decrescendo.tsx
│   │   ├── index.tsx
│   │   ├── loud-soft.tsx
│   │   ├── mpt.tsx
│   │   └── soft-loud.tsx
│   │
│   └── praat-detail/                # Praat 분석 상세
│       ├── components/
│       │   ├── PatientInfoSection.tsx
│       │   ├── PraatMetricsSections.tsx
│       │   ├── PraatMetricTile.tsx
│       │   ├── PraatSectionCard.tsx
│       │   ├── RecordingTabs.tsx
│       │   └── StatusBadge.tsx      # ⚠️ 중복: voice-training과 공통 컴포넌트
│       ├── hooks/
│       │   ├── index.ts
│       │   └── usePraat.ts
│       ├── pages/
│       │   └── PraatDetailPage.tsx
│       └── types/
│           ├── index.ts
│           └── types.ts
│
└── shared/                          # 공통 리소스
    ├── components/
    │   ├── display/
    │   │   └── WordDisplay.tsx
    │   ├── layout/
    │   │   ├── NavigationBar.tsx
    │   │   └── ProgressHeader.tsx
    │   ├── result/
    │   │   └── ResultHeader.tsx
    │   ├── routing/
    │   │   └── ProtectedRoute.tsx
    │   └── ui/                      # shadcn/ui 컴포넌트
    ├── hooks/
    │   └── useAlertDialog.tsx
    └── utils/
        ├── cn.ts
        ├── cookies.ts
        ├── dateFormatter.ts
        └── tts.ts
```

## 📊 현재 구조 분석

### 발견된 문제점

1. **중복 컴포넌트**
   - `VideoPlayerCard`, `LargeVideoPlayer`, `ResultVideoDisplay`: `practice/components/result`와 `result-detail/components/video`에 중복
   - `DetailedEvaluationItems`: `practice/components/result`와 `result-detail/components/evaluation`에 유사한 구현
   - `FeedbackCard`: `practice/components/result`와 `result-detail/components/feedback`에 유사한 구현
   - `StatusBadge`: `voice-training/components`와 `praat-detail/components`에 다른 구현

2. **구조적 문제**
   - `practice/components/result`와 `result-detail/components`가 거의 동일한 컴포넌트를 가지고 있음
   - 결과 관련 컴포넌트가 두 곳에 분산되어 있어 유지보수 어려움
   - 공통 컴포넌트가 `shared`로 이동되지 않음

3. **voice-training 구조**
   - 각 연습 타입별 페이지 파일이 루트에 있음 (`crescendo.tsx`, `decrescendo.tsx` 등)
   - `pages` 폴더가 없어 일관성 부족

## 🎯 개선안

### 1단계: 공통 비디오 컴포넌트 통합

**목표**: 비디오 관련 컴포넌트를 `shared`로 이동

```
shared/components/video/          # 새로 생성
├── VideoPlayerCard.tsx          # practice와 result-detail에서 이동
├── LargeVideoPlayer.tsx         # practice와 result-detail에서 이동
└── ResultVideoDisplay.tsx       # practice와 result-detail에서 이동
```

**영향받는 파일**:
- `features/practice/components/result/VideoPlayerCard.tsx` → 삭제
- `features/practice/components/result/LargeVideoPlayer.tsx` → 삭제
- `features/practice/components/result/ResultVideoDisplay.tsx` → 삭제
- `features/result-detail/components/video/*` → 삭제
- `features/practice/components/result/ResultComponent.tsx` → import 경로 수정
- `features/result-detail/pages/ResultDetailPage.tsx` → import 경로 수정

### 2단계: 결과 관련 컴포넌트 통합

**목표**: 결과 평가 및 피드백 컴포넌트를 `shared`로 이동하고 통합

```
shared/components/result/         # 새로 생성
├── DetailedEvaluationItems.tsx  # practice와 result-detail 통합 (feedback prop 추가)
├── DetailedEvaluationItemCard.tsx # result-detail에서 이동
├── FeedbackCard.tsx             # practice와 result-detail 통합
├── FeedbackSummary.tsx          # result-detail에서 이동
├── ImprovementPoints.tsx        # result-detail에서 이동
└── PronunciationScore.tsx       # result-detail에서 이동
```

**통합 전략**:
- `DetailedEvaluationItems`: `feedback` prop을 optional로 추가하여 practice와 result-detail 모두 지원
- `FeedbackCard`: `hideSections` prop으로 차이점 처리 (이미 구현됨)

**영향받는 파일**:
- `features/practice/components/result/DetailedEvaluationItems.tsx` → 삭제
- `features/practice/components/result/FeedbackCard.tsx` → 삭제
- `features/result-detail/components/evaluation/*` → 삭제
- `features/result-detail/components/feedback/*` → 삭제
- `features/practice/components/result/ResultComponent.tsx` → import 경로 수정
- `features/result-detail/pages/ResultDetailPage.tsx` → import 경로 수정

### 3단계: StatusBadge 통합

**목표**: StatusBadge 컴포넌트 통합

```
shared/components/display/
└── StatusBadge.tsx              # voice-training과 praat-detail 통합
```

**통합 전략**:
- 두 구현을 분석하여 하나의 유연한 컴포넌트로 통합
- 또는 두 가지 variant 제공 (simple, advanced)

**영향받는 파일**:
- `features/voice-training/components/StatusBadge.tsx` → 삭제
- `features/praat-detail/components/StatusBadge.tsx` → 삭제
- `features/voice-training/components/*` → import 경로 수정
- `features/praat-detail/components/*` → import 경로 수정

### 4단계: voice-training 구조 개선 (선택사항)

**옵션 A: pages 폴더 생성**
```
features/voice-training/
├── pages/
│   ├── crescendo.tsx
│   ├── decrescendo.tsx
│   ├── loud-soft.tsx
│   ├── soft-loud.tsx
│   └── mpt.tsx
├── components/
└── hooks/
```

**옵션 B: 현재 구조 유지**
- 간단한 구조이므로 현재 상태 유지 가능
- 각 페이지가 독립적이고 간단함

## 📋 개선 후 예상 구조

```
src/
├── shared/
│   └── components/
│       ├── video/              # 새로 생성
│       │   ├── VideoPlayerCard.tsx
│       │   ├── LargeVideoPlayer.tsx
│       │   └── ResultVideoDisplay.tsx
│       ├── result/             # 새로 생성
│       │   ├── DetailedEvaluationItems.tsx
│       │   ├── DetailedEvaluationItemCard.tsx
│       │   ├── FeedbackCard.tsx
│       │   ├── FeedbackSummary.tsx
│       │   ├── ImprovementPoints.tsx
│       │   └── PronunciationScore.tsx
│       └── display/
│           └── StatusBadge.tsx
│
├── features/
│   ├── practice/
│   │   ├── components/
│   │   │   ├── practice/       # 연습 관련만
│   │   │   │   ├── PracticeComponent.tsx
│   │   │   │   ├── RecordingControls.tsx
│   │   │   │   ├── RecordingPreview.tsx
│   │   │   │   ├── RecordingResult.tsx
│   │   │   │   └── RecordingTips.tsx
│   │   │   ├── result/         # 삭제 예정
│   │   │   │   └── ActionButtons.tsx (practice 전용)
│   │   │   └── TrainingLayout.tsx
│   │   ├── hooks/
│   │   ├── pages/
│   │   └── types/
│   │
│   ├── result-detail/
│   │   ├── components/         # 대부분 삭제, shared에서 import
│   │   ├── pages/
│   │   └── utils/
│   │
│   ├── voice-training/
│   │   ├── components/
│   │   ├── hooks/
│   │   └── pages/              # 선택사항
│   │
│   └── training-history/       # 변경 없음
```

## 🚀 실행 계획

### Phase 1: 비디오 컴포넌트 통합
1. `shared/components/video` 폴더 생성
2. `VideoPlayerCard`, `LargeVideoPlayer`, `ResultVideoDisplay` 이동
3. import 경로 업데이트
4. 중복 파일 삭제
5. 빌드 및 테스트

### Phase 2: 결과 컴포넌트 통합
1. `shared/components/result` 폴더 생성
2. `DetailedEvaluationItems` 통합 (feedback prop 추가)
3. `FeedbackCard` 통합
4. 나머지 컴포넌트 이동
5. import 경로 업데이트
6. 중복 파일 삭제
7. 빌드 및 테스트

### Phase 3: StatusBadge 통합
1. 두 구현 분석
2. 통합 컴포넌트 생성
3. import 경로 업데이트
4. 중복 파일 삭제
5. 빌드 및 테스트

### Phase 4: voice-training 구조 개선 (선택)
1. pages 폴더 생성 여부 결정
2. 필요시 페이지 파일 이동
3. import 경로 업데이트

## ✅ 기대 효과

1. **코드 중복 제거**: 동일한 컴포넌트의 중복 제거로 유지보수성 향상
2. **일관성 향상**: 공통 컴포넌트 사용으로 UI 일관성 보장
3. **재사용성 향상**: 다른 기능에서도 쉽게 재사용 가능
4. **구조 명확화**: 각 feature는 고유한 컴포넌트만 포함

## ⚠️ 주의사항

1. **점진적 마이그레이션**: 한 번에 모든 것을 변경하지 말고 단계적으로 진행
2. **테스트**: 각 단계마다 빌드 및 기능 테스트 필수
3. **의존성 확인**: import 경로 변경 시 모든 참조 확인
4. **타입 안정성**: TypeScript 타입 체크 통과 확인

