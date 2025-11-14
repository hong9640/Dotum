# Hooks 폴더 구조

이 프로젝트의 hooks는 기능과 페이지별로 체계적으로 구조화되어 있습니다.

## 📁 폴더 구조

```
hooks/
├── shared/                    # 공통 hooks (여러 페이지에서 사용)
│   ├── index.ts
│   ├── useAlertDialog.tsx
│   ├── useAsyncData.ts
│   ├── useMediaQuery.ts
│   └── useTTS.ts
├── login/                     # 로그인 페이지 hooks
│   └── index.ts
├── signup/                    # 회원가입 페이지 hooks
│   └── index.ts
├── training-session/          # 훈련 세션 hooks
│   └── index.ts
├── practice/                  # 발음 연습 페이지 hooks
│   ├── index.ts
│   ├── useCompositedVideoPolling.ts
│   ├── useMediaRecorder.ts
│   ├── usePracticeNavigation.ts
│   ├── usePracticeSession.ts
│   └── useVideoUpload.ts
├── voice-training/            # 발성 훈련 페이지 hooks
│   ├── index.ts
│   └── useAudioRecorder.ts
├── training-history/          # 훈련 기록 페이지 hooks
│   ├── index.ts
│   └── useCalendar.ts
├── training-history-detail/   # 훈련 기록 상세 페이지 hooks
│   ├── index.ts
│   └── useTrainingDayDetail.ts
└── result-detail/             # 결과 상세 페이지 hooks
    ├── index.ts
    └── usePraat.ts
```

## 🎯 폴더별 설명

### `hooks/shared/` - 공통 Hooks
여러 페이지에서 공통으로 사용되는 범용 hooks입니다.

- **useAlertDialog**: 알림 다이얼로그 표시 및 제어
- **useAsyncData**: 비동기 데이터 페칭 및 상태 관리
- **useMediaQuery**: 반응형 디자인을 위한 미디어 쿼리 감지
- **useTTS**: Text-to-Speech 기능

### `hooks/login/` - 로그인 Hooks
로그인 페이지에서 사용되는 hooks입니다.

### `hooks/signup/` - 회원가입 Hooks
회원가입 페이지에서 사용되는 hooks입니다.

### `hooks/training-session/` - 훈련 세션 Hooks
전역 훈련 세션 상태 관리 hooks입니다.

### `hooks/practice/` - 발음 연습 Hooks
단어/문장 발음 연습 페이지에서 사용되는 hooks입니다.

- **useMediaRecorder**: 비디오/오디오 녹화 제어
- **useCompositedVideoPolling**: Wav2Lip 합성 비디오 폴링
- **useVideoUpload**: 녹화 비디오 업로드 처리
- **usePracticeNavigation**: 훈련 아이템 간 네비게이션
- **usePracticeSession**: 발음 연습 세션 상태 관리

### `hooks/voice-training/` - 발성 훈련 Hooks
발성 훈련 페이지에서 사용되는 hooks입니다.

- **useAudioRecorder**: 오디오 녹음 제어

### `hooks/training-history/` - 훈련 기록 Hooks
훈련 기록 캘린더 페이지에서 사용되는 hooks입니다.

- **useCalendar**: 캘린더 상태 및 네비게이션

### `hooks/training-history-detail/` - 훈련 기록 상세 Hooks
특정 날짜의 훈련 기록 상세 페이지에서 사용되는 hooks입니다.

- **useTrainingDayDetail**: 일별 훈련 기록 상세 정보 관리

### `hooks/result-detail/` - 결과 상세 Hooks
훈련 결과 상세 페이지에서 사용되는 hooks입니다.

- **usePraat**: Praat 음성 분석 결과 폴링 및 표시

## 📝 사용 방법

### 공통 Hooks 사용
```typescript
// 공통 hooks는 @/hooks/shared 경로로 import
import { useAlertDialog, useTTS, useMediaQuery, useAsyncData } from '@/hooks/shared';

// 또는 개별 import
import { useAlertDialog } from '@/hooks/shared/useAlertDialog';
```

### 페이지별 Hooks 사용
```typescript
// 모든 페이지별 hooks는 @/hooks/[page-name] 경로로 import
import { useMediaRecorder, useVideoUpload } from '@/hooks/practice';
import { useAudioRecorder } from '@/hooks/voice-training';
import { useCalendar } from '@/hooks/training-history';
import { useTrainingDayDetail } from '@/hooks/training-history-detail';
import { usePraat } from '@/hooks/result-detail';
```

### 기능별 Hooks 사용
```typescript
// 로그인, 회원가입, 훈련 세션 등
import { useLogin } from '@/hooks/login';
import { useSignup } from '@/hooks/signup';
import { useTrainingSession } from '@/hooks/training-session';
```

## 🎨 디자인 원칙

1. **중앙 집중식 관리**: 모든 hooks는 `hooks/` 폴더 내에서 페이지별로 관리
2. **공통 hooks 분리**: 여러 페이지에서 사용되는 hooks는 `hooks/shared/` 폴더에 위치
3. **명확한 명명**: hook 이름은 기능을 명확히 표현 (`use` prefix 사용)
4. **index 파일**: 각 hooks 폴더에는 `index.ts` 파일로 export를 관리하여 import 경로 단순화

## 🔄 마이그레이션 가이드

기존 코드에서 새로운 구조로 마이그레이션할 때:

### Before (기존)
```typescript
import { useMediaRecorder } from './hooks/useMediaRecorder';
import { useCompositedVideoPolling } from '@/pages/practice/hooks/useCompositedVideoPolling';
import { useCalendar } from '../hooks/useCalendar';
```

### After (현재)
```typescript
import { useMediaRecorder, useCompositedVideoPolling } from '@/hooks/practice';
import { useCalendar } from '@/hooks/training-history';
```

## 📚 참고사항

- 모든 hooks는 TypeScript로 작성되어 있으며, 타입 안정성을 제공합니다.
- 각 hook은 단일 책임 원칙을 따르며, 명확한 목적을 가집니다.
- 복잡한 hook은 필요에 따라 추가 문서화가 되어 있습니다.
