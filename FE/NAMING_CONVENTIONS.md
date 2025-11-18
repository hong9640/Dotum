# 네이밍 규칙 (Naming Conventions)

## 📁 파일 및 폴더명

### 규칙: kebab-case 사용

모든 파일명과 폴더명은 **kebab-case**를 사용합니다.

#### ✅ 올바른 예시
```
api/
  training-session/
    session-item-search.ts
    current-item.ts
    composited-video-search.ts
    session-retry.ts
  practice/
    video-reupload.ts
  result-list/
    session-detail-search.ts
  training-history/
    daily-record-search.ts

pages/
  training-history-detail/
  result-list/
  practice/
```

#### ❌ 잘못된 예시
```
api/
  trainingSession/          # camelCase
    sessionItemSearch.ts    # camelCase
    currentItem.ts          # camelCase
```

## 🏷️ 도메인 용어 통일

### 세션 아이템 관련

#### 타입명
- ✅ `SessionItemResponse` - 세션 아이템 응답 타입 (통일된 타입명)
- ✅ `CurrentItemResponse` - 현재 진행 중인 아이템 응답 타입 (별도 API용)

#### 변수명
- ✅ `currentItem` - 현재 선택된/진행 중인 아이템 (로컬 변수명)
- ✅ `sessionItem` - 세션 아이템 (일반적인 변수명)
- ✅ `itemIndex` - 아이템 인덱스
- ✅ `currentItemIndex` - 현재 아이템 인덱스

#### API 함수명
- ✅ `getSessionItemByIndex` - 인덱스로 세션 아이템 조회
- ✅ `getCurrentItem` - 현재 진행 중인 아이템 조회

### 세션 관련

#### 타입명
- ✅ `TrainingSession` - 연습 세션 타입
- ✅ `CreateTrainingSessionRequest` - 세션 생성 요청
- ✅ `CreateTrainingSessionResponse` - 세션 생성 응답

#### 변수명
- ✅ `session` - 세션 객체
- ✅ `sessionId` - 세션 ID
- ✅ `sessionData` - 세션 데이터
- ✅ `sessionType` - 세션 타입 (word, sentence, vocal)

### 연습 관련

#### 타입명
- ✅ `TrainingItem` - 연습 아이템 타입 (세션 내 아이템)
- ✅ `TrainingHistory` - 연습 기록
- ✅ `TrainingSet` - 연습 세트

#### 변수명
- ✅ `trainingItem` - 연습 아이템
- ✅ `trainingHistory` - 연습 기록
- ✅ `trainingSet` - 연습 세트

## 📝 네이밍 패턴

### API 파일명
```
{도메인}-{기능}.ts

예시:
- session-item-search.ts
- video-reupload.ts
- daily-record-search.ts
```

### 컴포넌트 파일명
```
PascalCase.tsx

예시:
- TrainingLayout.tsx
- WordDisplay.tsx
- NavigationBar.tsx
```

### 훅 파일명
```
camelCase.ts (use 접두사)

예시:
- useMediaRecorder.ts
- usePracticeSession.ts
- useCompositedVideoPolling.ts
```

### 타입 파일명
```
kebab-case.ts

예시:
- video-state.ts
- upload-state.ts
- types.ts
```

## 🔄 변경 이력

### 2024년 변경사항
- 모든 API 파일명을 kebab-case로 통일
- 도메인 용어 `SessionItemResponse`로 통일
- import 경로 업데이트 완료

## 📚 참고

- React 컴포넌트는 PascalCase
- React 훅은 camelCase (use 접두사)
- 파일/폴더명은 kebab-case
- 타입명은 PascalCase
- 변수명은 camelCase

## 🔗 관련 문서

- [Utils vs Hooks 역할 기준](./UTILS_VS_HOOKS.md) - utils와 hooks의 역할 구분 기준

