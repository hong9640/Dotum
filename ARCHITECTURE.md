# 돋음(Dotum) 프로젝트 - 패키지 구조 & 아키텍처

## 📂 프로젝트 전체 구조

```
S13P31S201/
├── FE/                          # 프론트엔드 (React + Vite)
├── backend/                     # 백엔드 (FastAPI + Python)
├── ci/                          # CI/CD 설정 (Jenkins)
├── docker-compose.yml           # 전체 서비스 오케스트레이션
├── Jenkinsfile                  # Jenkins 파이프라인
├── DEPENDENCIES.md              # 의존성 문서
├── DESIGN_SYSTEM.md             # 디자인 시스템 문서
└── README.md                    # 프로젝트 개요
```

---

## 🎨 프론트엔드 아키텍처 (Frontend Architecture)

### 전체 구조
```
FE/
├── src/
│   ├── api/                     # API 통신 레이어
│   ├── assets/                  # 정적 리소스 (이미지, 아이콘)
│   ├── components/              # 재사용 가능 컴포넌트
│   ├── hooks/                   # 커스텀 React Hooks
│   ├── lib/                     # 유틸리티 라이브러리
│   ├── pages/                   # 페이지 컴포넌트
│   ├── stores/                  # 전역 상태 관리 (Zustand)
│   ├── types/                   # TypeScript 타입 정의
│   ├── utils/                   # 유틸리티 함수
│   ├── App.tsx                  # 루트 컴포넌트
│   ├── main.tsx                 # 엔트리 포인트
│   └── index.css                # 전역 스타일
├── public/                      # 퍼블릭 리소스
├── dist/                        # 빌드 결과물
├── package.json                 # 의존성 관리
├── vite.config.ts               # Vite 설정
├── tsconfig.json                # TypeScript 설정
├── tailwind.config.js           # Tailwind CSS 설정
├── eslint.config.js             # ESLint 설정
├── components.json              # shadcn/ui 설정
├── Dockerfile                   # Docker 이미지 설정
└── nginx.conf                   # Nginx 설정
```

---

### 📁 상세 디렉토리 구조

#### 1. **api/** - API 통신 레이어
```
api/
├── axios.ts                     # Axios 인스턴스 설정
├── login/
│   └── index.ts                 # 로그인 API
├── logout/
│   └── Logout.ts                # 로그아웃 API
├── signup/
│   └── index.ts                 # 회원가입 API
├── user/
│   └── index.ts                 # 사용자 정보 API
├── practice/
│   ├── index.ts                 # 연습 세션 API
│   └── videoReupload.ts         # 비디오 재업로드 API
├── training-session/
│   ├── index.ts                 # 훈련 세션 생성/조회
│   ├── currentItem.ts           # 현재 아이템 조회
│   ├── sessionItemSearch.ts     # 세션 아이템 검색
│   ├── sessionRetry.ts          # 세션 재시도
│   ├── praat.ts                 # Praat 분석 API
│   └── compositedVideoSearch.ts # 합성 비디오 조회
├── training-history/
│   ├── index.ts                 # 훈련 히스토리 조회
│   └── dailyRecordSearch.ts     # 일별 기록 조회
├── result-list/
│   └── sessionDetailSearch.ts   # 세션 상세 결과 조회
├── voice-training/
│   └── index.ts                 # 발성 훈련 API
└── README.md                    # API 문서
```

**아키텍처 패턴**: 
- 기능별 디렉토리 분리
- API 엔드포인트 별 파일 구성
- Axios 중앙 집중식 설정

---

#### 2. **components/** - 재사용 가능 컴포넌트
```
components/
├── ui/                          # shadcn/ui 기반 UI 컴포넌트
│   ├── button.tsx
│   ├── card.tsx
│   ├── dialog.tsx
│   ├── input.tsx
│   ├── form.tsx
│   ├── alert-dialog.tsx
│   ├── calendar.tsx
│   ├── carousel.tsx
│   ├── checkbox.tsx
│   ├── dropdown-menu.tsx
│   ├── label.tsx
│   ├── popover.tsx
│   ├── progress.tsx
│   ├── radio-group.tsx
│   ├── scroll-area.tsx
│   ├── select.tsx
│   ├── separator.tsx
│   ├── skeleton.tsx
│   ├── sonner.tsx               # Toast 알림
│   ├── spinner.tsx
│   ├── switch.tsx
│   ├── tabs.tsx
│   └── textarea.tsx
├── NavigationBar.tsx            # 네비게이션 바
├── ProgressHeader.tsx           # 진행 상황 헤더
├── ProtectedRoute.tsx           # 인증 보호 라우트
├── ScrollToTop.tsx              # 스크롤 탑 유틸
└── WordDisplay.tsx              # 단어 표시 컴포넌트
```

**설계 원칙**:
- Radix UI primitives 기반 접근성 우선
- Atomic Design 패턴 (ui/ 폴더는 Atoms)
- 재사용성과 확장성 고려

---

#### 3. **hooks/** - 커스텀 React Hooks
```
hooks/
├── login/
│   └── index.ts                 # 로그인 로직
├── signup/
│   └── index.ts                 # 회원가입 로직
├── training-session/
│   └── index.ts                 # 훈련 세션 로직
├── useAlertDialog.tsx           # 알림 다이얼로그 훅
├── useAudioRecorder.ts          # 오디오 녹음 훅
├── useCalendar.ts               # 캘린더 상태 관리
├── useCompositedVideoPolling.ts # 비디오 합성 폴링
├── useMediaQuery.ts             # 반응형 미디어 쿼리
├── useMediaRecorder.ts          # 미디어 녹화 훅
├── usePraat.ts                  # Praat 분석 훅
├── useTrainingDayDetail.ts      # 훈련 일별 상세
└── useTTS.ts                    # Text-to-Speech 훅
```

**Hook 패턴**:
- 비즈니스 로직과 UI 분리
- 상태 관리 캡슐화
- 재사용 가능한 로직 추상화

---

#### 4. **pages/** - 페이지 컴포넌트
```
pages/
├── home/
│   └── index.tsx                # 홈 페이지
├── login/
│   ├── components/              # 로그인 페이지 전용 컴포넌트
│   │   ├── LoginForm.tsx
│   │   ├── LoginFooter.tsx
│   │   └── ApiErrorDisplay.tsx
│   └── index.tsx
├── signup/
│   ├── components/              # 회원가입 페이지 전용 컴포넌트
│   │   ├── SignupForm.tsx
│   │   ├── SignupFooter.tsx
│   │   ├── FormField.tsx
│   │   ├── EmailVerificationField.tsx
│   │   └── ApiErrorDisplay.tsx
│   └── index.tsx
├── practice/                    # 연습 페이지 (핵심 기능)
│   ├── components/
│   │   ├── practice/            # 연습 중 컴포넌트
│   │   │   ├── PracticeComponent.tsx
│   │   │   ├── RecordingControls.tsx
│   │   │   ├── RecordingPreview.tsx
│   │   │   ├── RecordingResult.tsx
│   │   │   └── RecordingTips.tsx
│   │   ├── result/              # 결과 표시 컴포넌트
│   │   │   ├── ResultComponent.tsx
│   │   │   ├── ActionButtons.tsx
│   │   │   ├── DetailedEvaluationItems.tsx
│   │   │   ├── DetailedEvaluationItemCard.tsx
│   │   │   ├── FeedbackCard.tsx
│   │   │   ├── FeedbackSummary.tsx
│   │   │   ├── ImprovementPoints.tsx
│   │   │   ├── LargeVideoPlayer.tsx
│   │   │   ├── PronunciationScore.tsx
│   │   │   ├── ResultVideoDisplay.tsx
│   │   │   └── VideoPlayerCard.tsx
│   │   └── TrainingLayout.tsx
│   └── index.tsx
├── voice-training/              # 발성 훈련 페이지
│   ├── components/
│   │   ├── AudioPlayer.tsx
│   │   ├── AudioLevelGraph.tsx
│   │   ├── WaveRecorder.tsx
│   │   ├── RecordToggle.tsx
│   │   ├── StatusBadge.tsx
│   │   ├── PromptCardMPT.tsx
│   │   ├── PromptCardCrescendo.tsx
│   │   ├── PromptCardDecrescendo.tsx
│   │   ├── PromptCardLoudSoft.tsx
│   │   └── PromptCardSoftLoud.tsx
│   ├── index.tsx                # 발성 훈련 인트로
│   ├── mpt.tsx                  # MPT 훈련
│   ├── crescendo.tsx            # 크레셴도 훈련
│   ├── decrescendo.tsx          # 데크레셴도 훈련
│   ├── loud-soft.tsx            # 강-약 훈련
│   └── soft-loud.tsx            # 약-강 훈련
├── training-history/            # 훈련 히스토리 페이지
│   ├── components/
│   │   ├── Calendar.tsx
│   │   ├── CalendarGrid.tsx
│   │   ├── CalendarHeader.tsx
│   │   └── CalendarLegend.tsx
│   └── index.tsx
├── training-history-detail/     # 훈련 히스토리 상세
│   ├── components/
│   │   ├── Header.tsx
│   │   ├── EmptyState.tsx
│   │   ├── TrainingSetGrid.tsx
│   │   ├── TrainingSetCard.tsx
│   │   ├── ScoreChip.tsx
│   │   └── WordChip.tsx
│   ├── index.tsx
│   ├── types.ts
│   └── utils.ts
├── result-list/                 # 결과 목록 페이지
│   ├── components/
│   │   ├── ResultHeader.tsx
│   │   ├── AverageScoreCard.tsx
│   │   ├── MetricCard.tsx
│   │   ├── WordResultsList.tsx
│   │   ├── WordResultItem.tsx
│   │   └── ActionButtons.tsx
│   ├── index.tsx
│   ├── types.ts
│   └── utils.ts
├── result-detail/               # 결과 상세 페이지
│   └── index.tsx
└── praat-detail/                # Praat 분석 상세 페이지
    ├── components/
    │   ├── PatientInfoSection.tsx
    │   ├── PraatMetricsSections.tsx
    │   ├── PraatMetricTile.tsx
    │   ├── PraatSectionCard.tsx
    │   ├── RecordingTabs.tsx
    │   └── StatusBadge.tsx
    ├── index.tsx
    └── types.ts
```

**페이지 구조 패턴**:
- Feature-based 디렉토리 구조
- 페이지별 전용 컴포넌트는 `components/` 서브폴더
- 타입과 유틸리티는 같은 레벨에 배치

---

#### 5. **stores/** - 전역 상태 관리
```
stores/
└── practiceStore.ts             # 연습 세션 상태 관리 (Zustand)
```

**상태 관리 전략**:
- Zustand 기반 경량 상태 관리
- 서버 상태는 API 레이어에서 직접 관리
- 전역 상태 최소화 (연습 진행 상태만)

---

#### 6. **lib/** - 유틸리티 라이브러리
```
lib/
├── cookies.ts                   # 쿠키 관리 (인증 토큰)
└── utils.ts                     # 공통 유틸리티 (cn 함수 등)
```

---

#### 7. **types/** - TypeScript 타입
```
types/
└── api.ts                       # API 응답 타입 정의
```

---

### 🔄 프론트엔드 데이터 흐름

```
사용자 액션
    ↓
페이지 컴포넌트 (pages/)
    ↓
커스텀 Hook (hooks/)
    ↓
API 레이어 (api/)
    ↓
Axios 인스턴스
    ↓
백엔드 API
    ↓
응답 처리
    ↓
상태 업데이트 (useState / Zustand)
    ↓
UI 리렌더링
```

---

## ⚙️ 백엔드 아키텍처 (Backend Architecture)

### 전체 구조
```
backend/
├── api/
│   ├── core/                    # 핵심 설정
│   ├── src/                     # 비즈니스 로직
│   ├── utils/                   # 유틸리티
│   └── main.py                  # 애플리케이션 엔트리 포인트
├── migrations/                  # 데이터베이스 마이그레이션
├── requirements.txt             # Python 의존성
├── Dockerfile                   # Docker 이미지 설정
└── alembic.ini                  # Alembic 설정
```

---

### 📁 상세 디렉토리 구조

#### 1. **core/** - 핵심 설정
```
core/
├── config.py                    # 환경 변수 설정 (Pydantic Settings)
├── database.py                  # 데이터베이스 연결 설정
├── exception.py                 # 전역 예외 핸들러
├── logging.py                   # 로깅 설정
└── middleware.py                # 미들웨어 (CORS, 로깅 등)
```

**설계 원칙**:
- 설정의 중앙 집중화
- 환경 변수 기반 설정 (.env)
- 의존성 주입 패턴

---

#### 2. **src/** - 비즈니스 로직 (도메인별 구조)
```
src/
├── auth/                        # 인증 도메인
│   ├── auth_router.py           # 인증 라우터
│   ├── auth_schema.py           # 인증 스키마 (Pydantic)
│   └── auth_service.py          # 인증 비즈니스 로직
├── user/                        # 사용자 도메인
│   ├── user_router.py           # 사용자 라우터
│   ├── user_schema.py           # 사용자 스키마
│   ├── user_service.py          # 사용자 비즈니스 로직
│   ├── user_model.py            # 사용자 모델 (SQLAlchemy)
│   └── user_enum.py             # 사용자 관련 Enum
├── token/                       # 토큰 도메인
│   └── token_model.py           # JWT 토큰 모델
└── train/                       # 훈련 도메인 (핵심)
    ├── models/                  # 데이터베이스 모델
    ├── repositories/            # 데이터 접근 계층
    ├── routes/                  # API 라우터
    ├── schemas/                 # 요청/응답 스키마
    └── services/                # 비즈니스 로직
```

---

#### 3. **train/** - 훈련 도메인 (상세)
```
train/
├── models/                      # SQLAlchemy 모델
│   ├── media.py                 # 미디어 파일 모델
│   ├── praat.py                 # Praat 분석 결과 모델
│   ├── sentences.py             # 문장 모델
│   ├── words.py                 # 단어 모델
│   ├── training_session.py      # 훈련 세션 모델
│   └── training_item.py         # 훈련 아이템 모델
├── repositories/                # Repository 패턴
│   ├── base.py                  # 베이스 Repository
│   ├── words.py                 # 단어 Repository
│   ├── sentences.py             # 문장 Repository
│   ├── training_sessions.py     # 세션 Repository
│   └── training_items.py        # 아이템 Repository
├── routes/                      # API 엔드포인트
│   ├── words.py                 # 단어 관련 API
│   ├── sentences.py             # 문장 관련 API
│   ├── training_sessions.py     # 세션 관련 API
│   └── media.py                 # 미디어 관련 API
├── schemas/                     # Pydantic 스키마
│   ├── common.py                # 공통 스키마
│   ├── words.py                 # 단어 스키마
│   ├── sentences.py             # 문장 스키마
│   ├── training_sessions.py     # 세션 스키마
│   ├── training_items.py        # 아이템 스키마
│   ├── praat.py                 # Praat 스키마
│   └── media.py                 # 미디어 스키마
└── services/                    # 비즈니스 로직
    ├── words.py                 # 단어 서비스
    ├── sentences.py             # 문장 서비스
    ├── training_sessions.py     # 세션 서비스
    ├── praat.py                 # Praat 분석 서비스
    ├── video_processor.py       # 비디오 처리 서비스
    ├── media.py                 # 미디어 서비스
    └── gcs_service.py           # Google Cloud Storage 서비스
```

---

### 🏗️ 백엔드 아키텍처 패턴

#### **계층형 아키텍처 (Layered Architecture)**

```
┌─────────────────────────────────────┐
│   API Layer (routes/)               │  ← HTTP 요청/응답
│   - FastAPI Router                  │
│   - 요청 검증 (Pydantic)             │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│   Service Layer (services/)         │  ← 비즈니스 로직
│   - 도메인 로직 구현                  │
│   - 외부 서비스 연동                  │
│   - 트랜잭션 관리                     │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│   Repository Layer (repositories/)  │  ← 데이터 접근
│   - CRUD 작업 추상화                 │
│   - 쿼리 로직 캡슐화                  │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│   Model Layer (models/)             │  ← 데이터 모델
│   - SQLAlchemy ORM                  │
│   - 테이블 정의                       │
└─────────────────────────────────────┘
```

---

### 🔄 백엔드 요청 처리 흐름

```
클라이언트 요청
    ↓
FastAPI Router (routes/)
    ↓
Pydantic Schema 검증 (schemas/)
    ↓
Service Layer (services/)
    ↓
Repository Layer (repositories/)
    ↓
SQLAlchemy Model (models/)
    ↓
PostgreSQL Database
    ↓
응답 생성 (schemas/)
    ↓
클라이언트 응답
```

---

### 🗄️ 데이터베이스 마이그레이션

```
migrations/
├── versions/                    # 마이그레이션 버전 파일들
│   ├── abc1cec616ad_first_alembic.py
│   ├── e8f57ca4c4e0_upgrade_user_table.py
│   ├── 51f296d63302_unified_training_sessions.py
│   └── ... (총 58개 마이그레이션)
├── env.py                       # Alembic 환경 설정
└── script.py.mako               # 마이그레이션 템플릿
```

**마이그레이션 전략**:
- Alembic 기반 버전 관리
- 자동 마이그레이션 생성
- 롤백 가능한 구조

---

## 🐳 인프라 아키텍처 (Infrastructure)

### Docker Compose 서비스 구성

```yaml
services:
  ┌──────────────────────────────────────────┐
  │  Frontend (Nginx + React)                │
  │  Port: 80, 443                           │
  │  └─ Vite Build → Nginx 정적 서빙         │
  └──────────────────────────────────────────┘
                   ↓ HTTP
  ┌──────────────────────────────────────────┐
  │  Backend (FastAPI)                       │
  │  Port: 8000                              │
  │  └─ Uvicorn ASGI Server                  │
  └──────────────────────────────────────────┘
                   ↓ SQL
  ┌──────────────────────────────────────────┐
  │  PostgreSQL                              │
  │  Port: 5432                              │
  │  └─ 데이터베이스                          │
  └──────────────────────────────────────────┘

  ┌──────────────────────────────────────────┐
  │  Jenkins (CI/CD)                         │
  │  Port: 8080, 50000                       │
  └──────────────────────────────────────────┘

  ┌──────────────────────────────────────────┐
  │  Portainer (Docker UI)                   │
  │  Port: 55555                             │
  └──────────────────────────────────────────┘
```

---

### 네트워크 아키텍처

```
                    Internet
                       ↓
                 [Nginx:443]
                       ↓
         ┌─────────────┴─────────────┐
         ↓                           ↓
   [React SPA]              [FastAPI Backend:8000]
                                     ↓
                            [PostgreSQL:5432]
                                     ↓
                          [Google Cloud Storage]
```

---

## 📊 주요 기능별 아키텍처

### 1. 인증 흐름 (Authentication Flow)

```
[Client]
   ↓ POST /api/v1/auth/login
[Backend: auth_router]
   ↓
[auth_service.authenticate()]
   ↓
[user_model 조회]
   ↓
[JWT 토큰 생성]
   ↓
[Cookie 설정]
   ↓
[Client: 토큰 저장]
```

---

### 2. 훈련 세션 생성 흐름

```
[Client: 단어/문장 훈련 시작]
   ↓ POST /api/v1/train/sessions
[Backend: training_sessions.py (routes)]
   ↓
[training_sessions.py (services)]
   ↓ create_session()
[training_sessions.py (repositories)]
   ↓ 세션 DB 저장
[words/sentences.py (repositories)]
   ↓ 랜덤 단어/문장 조회
[training_items.py (repositories)]
   ↓ 훈련 아이템 생성
[PostgreSQL: 트랜잭션 커밋]
   ↓
[Client: 세션 ID 수신]
```

---

### 3. 음성 녹음 & 분석 흐름

```
[Client: 음성 녹음]
   ↓ RecordRTC
[Client: 비디오 파일 생성]
   ↓ POST /api/v1/train/media
[Backend: media.py (routes)]
   ↓
[gcs_service.py: GCS 업로드]
   ↓
[video_processor.py: 비디오 합성]
   ↓
[praat.py (services): 음성 분석]
   ↓ praat-parselmouth
[praat_model: 분석 결과 저장]
   ↓
[Client: 결과 조회 (폴링)]
```

---

### 4. 훈련 히스토리 조회 흐름

```
[Client: 캘린더 페이지]
   ↓ GET /api/v1/train/history
[Backend: training_sessions.py (routes)]
   ↓
[training_sessions.py (services)]
   ↓ get_user_training_history()
[training_sessions.py (repositories)]
   ↓ 날짜별 세션 집계
[PostgreSQL: GROUP BY created_at::date]
   ↓
[Client: 캘린더 렌더링]
```

---

## 🔐 보안 아키텍처

### 인증 & 권한
- **JWT 토큰**: HttpOnly Cookie 저장
- **Access Token**: 30분 만료
- **비밀번호**: Passlib bcrypt 해싱
- **CORS**: 허용된 Origin만 접근

### 데이터 보호
- **환경 변수**: .env 파일 분리
- **민감 정보**: GCS 서비스 키 별도 관리
- **SQL Injection**: SQLAlchemy ORM 사용

---

## 📈 확장성 고려사항

### 프론트엔드
- **코드 스플리팅**: Vite 자동 최적화
- **이미지 최적화**: GCS CDN 활용
- **캐싱**: Nginx 정적 파일 캐싱

### 백엔드
- **비동기 처리**: FastAPI + asyncpg
- **Connection Pool**: SQLAlchemy 연결 풀
- **분산 저장소**: Google Cloud Storage

### 데이터베이스
- **인덱싱**: 주요 쿼리 최적화
- **마이그레이션**: Alembic 버전 관리
- **백업**: Docker Volume 영구 저장

---

## 🚀 배포 전략

### CI/CD 파이프라인

```
[Git Push]
   ↓
[Jenkins: Webhook Trigger]
   ↓
[Build Stage]
   ├─ Frontend: npm install → npm run build
   └─ Backend: pip install -r requirements.txt
   ↓
[Docker Build]
   ├─ docker build FE/
   └─ docker build backend/
   ↓
[Docker Compose Up]
   ├─ Frontend Container (Port 80, 443)
   ├─ Backend Container (Port 8000)
   └─ PostgreSQL Container (Port 5432)
   ↓
[Health Check]
   ↓
[Deploy Complete]
```

---

## 📚 코딩 컨벤션

### 프론트엔드
- **파일명**: PascalCase (컴포넌트), camelCase (유틸)
- **컴포넌트**: 함수형 컴포넌트 + Hooks
- **타입**: interface 우선, type은 Union/Intersection
- **스타일**: Tailwind CSS 유틸리티 클래스

### 백엔드
- **파일명**: snake_case
- **클래스**: PascalCase
- **함수**: snake_case
- **타입 힌트**: 모든 함수에 타입 힌트 필수

---

**마지막 업데이트**: 2025-11-13  
**아키텍처 버전**: 1.0.0  
**프로젝트**: 돋음 (Dotum) - 발음 교정 서비스

