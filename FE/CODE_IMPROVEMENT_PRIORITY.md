# 폴더 구조 개선안 계획 (v2)

## 📁 현재 아키텍처 트리 구조

```txt
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
현재 구조 분석
발견된 문제점

중복 컴포넌트

VideoPlayerCard, LargeVideoPlayer, ResultVideoDisplay: practice/components/result와 result-detail/components/video에 중복

DetailedEvaluationItems: practice/components/result와 result-detail/components/evaluation에 유사한 구현

FeedbackCard: practice/components/result와 result-detail/components/feedback에 유사한 구현

StatusBadge: voice-training/components와 praat-detail/components에 다른 구현

구조적 문제

practice/components/result와 result-detail/components가 거의 동일한 컴포넌트를 가지고 있음

결과 관련 컴포넌트가 두 곳에 분산되어 있어 유지보수 어려움

공통 컴포넌트가 shared로 이동되지 않음

voice-training 구조

각 연습 타입별 페이지 파일이 루트에 있음 (crescendo.tsx, decrescendo.tsx 등)

pages 폴더가 없어 일관성 부족

🔗 의존성 및 타입 설계 원칙

공통 컴포넌트를 shared로 이동할 때, 레이어/의존성 규칙을 명확히 해서 나중에 꼬이지 않도록 한다.

의존 방향

허용: src/features/** → src/shared/**

금지: src/shared/** → src/features/**

즉, shared 내부에서는 어떤 feature 코드도 import 하지 않는다.

shared의 역할

shared/components/**: 순수 프레젠테이션(UI) 컴포넌트만 위치

props로 데이터/콜백만 받고, UI만 그린다.

여기서는 API 호출, react-query, zustand, 라우팅, feature 전용 hooks 등을 사용하지 않는다.

shared/utils/**: 공통 유틸 함수

shared/types/**: 여러 feature에서 공통으로 사용하는 타입/인터페이스 정의

공통 타입 분리

현재 practice, result-detail, result-list 등에서 공통으로 사용하는 결과/평가 관련 타입들은

먼저 shared/types/result.ts (또는 유사한 파일)로 승격시킨다.

이후 shared/components/result/**는 반드시 shared/types/**만 import하고,
features/**의 타입을 import 하지 않는다.

리팩토링 순서

특히 Phase 2(결과 컴포넌트 통합) 시작 전에,

공통 타입을 shared/types로 분리하는 작업을 선행 작업으로 둔다.

이 순서를 지키면 shared로 옮길 때 순환 의존성(circular dependency) 리스크를 줄일 수 있다.

🎯 개선안
1단계: 공통 비디오 컴포넌트 통합

목표: 비디오 관련 컴포넌트를 shared로 이동

폴더 이름을 video가 아니라 **media**로 두어,
추후 오디오 플레이어, 파형 뷰어 등도 함께 수용할 수 있게 확장성을 열어둔다.

shared/components/media/          # 새로 생성
├── VideoPlayerCard.tsx          # practice와 result-detail에서 이동/통합
├── LargeVideoPlayer.tsx         # practice와 result-detail에서 이동/통합
└── ResultVideoDisplay.tsx       # practice와 result-detail에서 이동/통합


영향받는 파일:

features/practice/components/result/VideoPlayerCard.tsx → 삭제

features/practice/components/result/LargeVideoPlayer.tsx → 삭제

features/practice/components/result/ResultVideoDisplay.tsx → 삭제

features/result-detail/components/video/* → 삭제

features/practice/components/result/ResultComponent.tsx → import 경로 수정

features/result-detail/pages/ResultDetailPage.tsx → import 경로 수정

⚠️ 이동 시, VideoPlayerCard 등에서 feature 전용 훅이나 라우팅 로직을 사용하고 있다면
해당 부분은 페이지/컨테이너에서 처리하고 props로 내려주는 구조로 바꾼 뒤 shared로 이동한다.

2단계: 결과 관련 컴포넌트 통합

목표: 결과 평가 및 피드백 컴포넌트를 shared로 이동하고 통합

shared/types/
└── result.ts                    # 결과/평가/피드백 공통 타입 정의

shared/components/result/        # 새로 생성
├── DetailedEvaluationItems.tsx  # practice와 result-detail 통합 (variant/props로 분기)
├── DetailedEvaluationItemCard.tsx
├── FeedbackCard.tsx             # practice와 result-detail 통합
├── FeedbackSummary.tsx
├── ImprovementPoints.tsx
└── PronunciationScore.tsx


사전 작업(필수): 타입 통합

features/practice, features/result-detail, features/result-list에서
결과/평가/피드백 컴포넌트들이 사용하는 타입/인터페이스를 조사한다.

이 중 여러 feature에서 공유하는 타입만 골라서
shared/types/result.ts로 옮긴다.

각 feature와 컴포넌트는 이제 이 shared 타입을 import하도록 변경한다.

shared/components/result/**는 반드시 shared/types/result만 사용하고,
features/**의 타입은 import 하지 않는다.

통합 전략:

DetailedEvaluationItems

practice와 result-detail에서 props 차이가 있다면,

variant: 'practice' | 'detail' 같은 prop을 두거나,

feedback? 같은 optional props로 분기 처리.

조건 분기가 과하게 복잡해지면, 추후 variant 기반 분리로 리팩토링.

FeedbackCard

hideSections, mode 같은 prop으로 practice/result-detail 차이를 흡수.

내부에서 API 호출이나 세션 관리 X → 오직 표시/레이아웃만 담당.

영향받는 파일:

features/practice/components/result/DetailedEvaluationItems.tsx → 삭제

features/practice/components/result/FeedbackCard.tsx → 삭제

features/result-detail/components/evaluation/* → 삭제

features/result-detail/components/feedback/* → 삭제

features/practice/components/result/ResultComponent.tsx → import 경로 수정

features/result-detail/pages/ResultDetailPage.tsx → import 경로 수정

3단계: StatusBadge 통합

목표: StatusBadge 컴포넌트 통합

shared/components/display/
└── StatusBadge.tsx              # voice-training과 praat-detail 통합


통합 전략:

두 구현(voice-training, praat-detail)을 비교해서 공통 인터페이스를 정의:

type StatusBadgeProps = {
  label: string;
  status: 'success' | 'warning' | 'error' | 'neutral';
  variant?: 'simple' | 'detailed' | 'filled' | 'outlined';
};


스타일/표현 차이는 variant와 status로 제어.

비즈니스 로직/상태는 feature 레벨에서 처리하고, Badge는 단순 표시만 담당.

영향받는 파일:

features/voice-training/components/StatusBadge.tsx → 삭제

features/praat-detail/components/StatusBadge.tsx → 삭제

features/voice-training/components/* → import 경로 수정

features/praat-detail/components/* → import 경로 수정

4단계: voice-training 구조 개선 (선택사항, 후순위)

옵션 A: pages 폴더 생성

features/voice-training/
├── pages/
│   ├── crescendo.tsx
│   ├── decrescendo.tsx
│   ├── loud-soft.tsx
│   ├── soft-loud.tsx
│   └── mpt.tsx
├── components/
└── hooks/


다른 feature(practice, training-history, praat-detail 등)와 구조를 맞추기 위해,
장기적으로 적용하면 인지 부하 감소에 도움이 됨.

다만 이 작업은 라우팅/페이지 구조 리팩토링과 함께 별도 PR로 진행해도 충분하므로,
이번 shared 리팩토링과는 분리된 후순위 작업으로 둔다.

옵션 B: 현재 구조 유지

당장 급하지 않다면 유지 가능.

추후 라우팅/네비게이션 리팩토링 타이밍에 Option A로 이동 고려.

📋 개선 후 예상 구조
src/
├── shared/
│   ├── components/
│   │   ├── media/               # 새로 생성 (비디오/오디오 등)
│   │   │   ├── VideoPlayerCard.tsx
│   │   │   ├── LargeVideoPlayer.tsx
│   │   │   └── ResultVideoDisplay.tsx
│   │   ├── result/              # 결과 도메인 UI 모듈
│   │   │   ├── DetailedEvaluationItems.tsx
│   │   │   ├── DetailedEvaluationItemCard.tsx
│   │   │   ├── FeedbackCard.tsx
│   │   │   ├── FeedbackSummary.tsx
│   │   │   ├── ImprovementPoints.tsx
│   │   │   └── PronunciationScore.tsx
│   │   ├── display/
│   │   │   ├── WordDisplay.tsx
│   │   │   └── StatusBadge.tsx
│   │   ├── layout/
│   │   │   ├── NavigationBar.tsx
│   │   │   └── ProgressHeader.tsx
│   │   ├── routing/
│   │   │   └── ProtectedRoute.tsx
│   │   └── ui/                  # shadcn/ui 컴포넌트
│   ├── hooks/
│   │   └── useAlertDialog.tsx
│   ├── types/
│   │   └── result.ts            # 결과/평가/피드백 공통 타입
│   └── utils/
│       ├── cn.ts
│       ├── cookies.ts
│       ├── dateFormatter.ts
│       └── tts.ts
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
│   │   │   ├── result/         # 추후 ActionButtons만 남기고 삭제 예정
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
│   ├── result-list/
│   │   ├── components/
│   │   ├── pages/
│   │   └── types/
│   │
│   ├── voice-training/
│   │   ├── components/         # StatusBadge는 shared 사용
│   │   ├── hooks/
│   │   └── pages/              # 선택사항 (도입 시)
│   │
│   ├── praat-detail/
│   │   ├── components/         # StatusBadge는 shared 사용
│   │   ├── hooks/
│   │   ├── pages/
│   │   └── types/
│   │
│   └── training-history/       # 변경 없음
│
└── ...

🚀 실행 계획
Phase 1: 비디오 컴포넌트 통합

shared/components/media 폴더 생성

VideoPlayerCard, LargeVideoPlayer, ResultVideoDisplay를 shared로 이동/통합

feature 전용 로직이 있다면 페이지/컨테이너로 끌어올리고,
shared 컴포넌트는 props 기반 UI만 남긴다.

practice/result-detail에서 import 경로 업데이트

중복 파일 삭제

tsc --noEmit + 빌드/기능 테스트

Phase 2: 결과 컴포넌트 및 타입 통합

공통 타입 분리 (선행 작업)

practice/result-detail/result-list에서 사용하는 결과/평가 관련 타입 식별

공통으로 사용하는 타입을 shared/types/result.ts로 이동

기존 feature 코드들이 이 shared 타입을 사용하도록 수정

shared/components/result 폴더 생성

DetailedEvaluationItems, FeedbackCard를 통합

variant/optional props로 두 feature에서 모두 사용 가능하도록 설계

나머지 결과 UI 컴포넌트 이동

DetailedEvaluationItemCard

FeedbackSummary

ImprovementPoints

PronunciationScore

practice/result-detail에서 import 경로 업데이트

기존 중복 파일 삭제

타입 체크 + 빌드 + 주요 플로우 테스트

Phase 3: StatusBadge 통합

shared/components/display/StatusBadge.tsx 생성

voice-training / praat-detail의 StatusBadge 구현 비교

공통 props/variant로 통합 컴포넌트 구현

두 feature에서 shared StatusBadge를 사용하도록 교체

기존 StatusBadge 파일 삭제

타입 체크 + 빌드 + 주요 플로우 테스트

Phase 4: voice-training 구조 개선 (선택)

팀 컨벤션에 따라 features/voice-training/pages 도입 여부 결정

도입 시:

crescendo.tsx, decrescendo.tsx, mpt.tsx, loud-soft.tsx, soft-loud.tsx를 pages로 이동

라우팅 설정 및 import 경로 업데이트

이 Phase는 shared 리팩토링과 분리하여,
라우팅/페이지 구조 리팩토링 시점에 따로 진행하는 것을 권장

✅ 기대 효과

코드 중복 제거

동일한 컴포넌트의 중복 제거로 유지보수성 향상

일관성 향상

공통 컴포넌트 사용으로 UI/UX 일관성 보장

재사용성 향상

새로운 feature에서도 쉽게 공통 UI를 재사용 가능

구조 명확화

각 feature는 고유한 플로우와 로직에 집중,
shared는 공통 UI/타입만 담당

⚠️ 주의사항

점진적 마이그레이션

한 번에 모든 것을 변경하지 말고 Phase 단위로 진행

테스트 필수

각 Phase마다 tsc, 빌드, 핵심 플로우(연습 → 결과 → 상세) 수동 테스트

의존성 확인

import 경로 변경 시, shared에서 features를 참조하지 않는지 항상 확인

타입 안정성

TypeScript 타입 체크를 통과하는 상태를 유지

공통 타입 위치

여러 feature가 공유하는 타입은 shared/types로 승격시켜 관리

shared의 순수성 유지

shared/components는 UI만 담당하도록 유지하고,
비즈니스 로직/데이터 로딩/라우팅은 항상 features 레이어에서 처리