# API 디렉토리 구조

이 디렉토리는 프로젝트의 모든 API 호출을 관리합니다.

## 구조

```
src/api/
├── axios.ts          # Axios 인스턴스 설정
├── signup/           # 회원가입 API
│   ├── index.ts
│   └── index.md
└── README.md         # 이 파일
```

## 사용 방법

### 1. Axios 클라이언트 사용

모든 API 호출은 `src/api/axios.ts`에서 제공하는 `apiClient`를 사용합니다.

```typescript
import { apiClient } from "@/shared/api/axios";

// GET 요청
const response = await apiClient.get("/endpoint");

// POST 요청
const response = await apiClient.post("/endpoint", data);

// PUT 요청
const response = await apiClient.put("/endpoint", data);

// DELETE 요청
const response = await apiClient.delete("/endpoint");
```

### 2. 새로운 API 추가하기

1. `src/api/[기능명]/` 디렉토리 생성
2. `index.ts` 파일에 API 함수 정의
3. 타입 정의 및 에러 처리 포함

**예시:**
```typescript
import { apiClient } from "../axios";

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  user: {
    id: string;
    name: string;
  };
}

export const login = async (data: LoginRequest): Promise<LoginResponse> => {
  const response = await apiClient.post<LoginResponse>("/auth/login", data);
  return response.data;
};
```

### 3. 환경 변수 설정

`.env` 파일에 Base URL을 설정할 수 있습니다:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

설정하지 않으면 기본값 `http://localhost:8000/api/v1`이 사용됩니다.

## 규칙

- ✅ 모든 API 호출은 `apiClient`를 사용합니다
- ✅ fetch 대신 axios를 사용합니다
- ✅ 타입을 명시적으로 정의합니다
- ✅ 에러 처리를 포함합니다
- ✅ JSDoc 주석을 작성합니다

## 예시

회원가입 API 예시를 참고하세요: `src/api/signup/index.ts`

