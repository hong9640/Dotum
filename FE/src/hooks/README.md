# Hooks 폴더 구조

이 프로젝트의 hooks는 기능과 페이지별로 체계적으로 구조화되어 있습니다.

## 📁 폴더 구조

```
hooks/
└── README.md                  # 현재 파일 (문서 전용)
```

> 대부분의 실제 hook 구현체는 이제 `src/features/{domain}/hooks/` 또는  
> `src/shared/hooks/`(공용) 아래에 위치합니다.

## 🎯 폴더별 설명

### `shared/hooks/` - 공통 Hooks
여러 페이지에서 공통으로 사용되는 범용 hooks입니다. (실제 위치: `src/shared/hooks/`)

- **useAlertDialog**: 알림 다이얼로그 표시 및 제어
- **useAsyncData**: 비동기 데이터 페칭 및 상태 관리
- **useMediaQuery**: 반응형 디자인을 위한 미디어 쿼리 감지
- **useTTS**: Text-to-Speech 기능

### Auth Hooks (`src/features/auth/hooks/`)
로그인, 회원가입 등 인증 도메인 훅입니다.

### Voice Training Hooks (`src/features/voice-training/hooks/`)
발성 연습 페이지에서 사용되는 훅입니다. 예) **useAudioRecorder**.

### Result Detail Hooks (`src/features/praat-detail/hooks/`)
Praat 분석/결과 상세에 필요한 훅입니다. 예) **usePraat**.

## 📝 사용 방법

### 공통 Hooks 사용
```typescript
// 공통 hooks는 @/shared/hooks 경로로 import
import { useAlertDialog, useTTS, useMediaQuery, useAsyncData } from '@/shared/hooks';

// 또는 개별 import
import { useAlertDialog } from '@/shared/hooks/useAlertDialog';
```

### 페이지별 Hooks 사용
```typescript
// 모든 페이지별 hooks는 @/features/[feature-name]/hooks 경로로 import
import { useMediaRecorder, useVideoUpload } from '@/features/practice/hooks';
import { useAudioRecorder } from '@features/voice-training/hooks';
import { useCalendar, useTrainingDayDetail } from '@/features/training-history/hooks';
import { usePraat } from '@/features/praat-detail/hooks';
```

### 기능별 Hooks 사용
```typescript
// 로그인, 회원가입, 연습 세션 등
import { useLogin } from '@features/auth/hooks/useLogin';
import { useSignup } from '@features/auth/hooks/useSignup';
import { useTrainingSession } from '@/features/training-session/hooks';
```

## 🎨 디자인 원칙

1. **도메인별 관리**: 기능별 훅은 `src/features/{domain}/hooks/`에 위치
2. **공통 훅 분리**: 여러 도메인에서 재사용되는 훅은 `src/shared/hooks/`에 위치
3. **명확한 명명**: hook 이름은 기능을 명확히 표현 (`use` prefix 사용)
4. **index 파일**: 각 hooks 폴더에는 `index.ts` 파일로 export를 관리하여 import 경로 단순화

## 🔄 마이그레이션 가이드

기존 코드에서 새로운 구조로 마이그레이션할 때:

### Before (기존)
```typescript
import { useMediaRecorder } from '@/hooks/practice';
import { useCompositedVideoPolling } from '@/hooks/practice';
import { useCalendar } from '@/hooks/training-history';
```

### After (현재)
```typescript
import { useMediaRecorder, useCompositedVideoPolling } from '@/features/practice/hooks';
import { useCalendar } from '@/features/training-history/hooks';
```

## 📚 참고사항

- 모든 hooks는 TypeScript로 작성되어 있으며, 타입 안정성을 제공합니다.
- 각 hook은 단일 책임 원칙을 따르며, 명확한 목적을 가집니다.
- 복잡한 hook은 필요에 따라 추가 문서화가 되어 있습니다.
