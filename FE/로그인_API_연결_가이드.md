# 로그인 API 연결 가이드

## 📋 목차
1. [API 파일 생성](#1-api-파일-생성)
2. [타입 정의](#2-타입-정의)
3. [API 함수 구현](#3-api-함수-구현)
4. [Hook 생성](#4-hook-생성)
   - 4-1. [필요한 Import 추가](#4-1-필요한-import-추가)
   - 4-2-1. [Zod란?](#4-2-1-zod란)
   - 4-2-2. [Zod 유효성 검사 스키마 정의](#4-2-2-zod-유효성-검사-스키마-정의)
   - 4-3. [Hook 인터페이스 정의](#4-3-hook-인터페이스-정의)
   - 4-4. [Hook 함수 구현](#4-4-hook-함수-구현)
5. [UI 컴포넌트 분리 및 수정](#5-ui-컴포넌트-분리-및-수정)
   - 5-1. [컴포넌트 폴더 생성](#5-1-컴포넌트-폴더-생성)
   - 5-2. [ApiErrorDisplay 컴포넌트 생성](#5-2-apierrordisplay-컴포넌트-생성)
   - 5-3. [LoginForm 컴포넌트 생성](#5-3-loginform-컴포넌트-생성)
   - 5-4. [LoginFooter 컴포넌트 생성](#5-4-loginfooter-컴포넌트-생성)
   - 5-5. [메인 페이지 수정](#5-5-메인-페이지-수정)
6. [토큰 저장 기능 추가](#6-토큰-저장-기능-추가)
7. [테스트](#7-테스트)

---

## 1. API 파일 생성

### 목표
로그인 API 함수를 정의하는 파일을 생성합니다.

### 작업 파일
**생성**: `src/api/login/index.ts`

### 1-1. 파일 생성 및 기본 구조 작성

```typescript
import { apiClient } from "../axios";  // axios 기반 API 클라이언트 (baseURL, 인터셉터 포함)

// 로그인 API 타입 정의는 다음 단계에서 추가합니다.

// 로그인 API 함수는 다음 단계에서 추가합니다.
```

---

## 2. 타입 정의

### 목표
로그인 API의 요청과 응답 타입을 정의합니다.

### 작업 파일
`src/api/login/index.ts`

### 2-1. 요청 타입 정의

```typescript
// 로그인 요청 타입
export interface LoginRequest {
  username: string;
  password: string;
}
```

### 2-2. 응답 타입 정의

```typescript
// 토큰 정보 타입
export interface TokenInfo {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

// 사용자 정보 타입
export interface UserInfo {
  id: number;
  username: string;
  name: string;
  role: string;
}

// 로그인 성공 응답 타입
export interface LoginSuccessResponse {
  status: "SUCCESS";
  data: {
    user: UserInfo;
    token: TokenInfo;
  };
}

// 로그인 실패 응답 타입
export interface LoginErrorResponse {
  status: "FAIL";
  error: {
    code: string;
    message: string;
  };
}

// 로그인 응답 타입 (성공 또는 실패)
export type LoginResponse = LoginSuccessResponse | LoginErrorResponse;
```

---

## 3. API 함수 구현

### 목표
로그인 API 호출 함수를 구현합니다.

### 작업 파일
`src/api/login/index.ts`

### 3-1. 에러 매핑 테이블 추가

`Record<string, string>` 타입을 사용하여 유연하게 에러 메시지를 관리합니다.
불필요한 타입 캐스팅을 피하고 코드를 단순화합니다.

```typescript
// 에러 매핑 테이블
const ERROR_MAPPING: Record<string, string> = {
  INVALID_CREDENTIALS: "아이디 또는 비밀번호가 올바르지 않습니다.",
};
```

### 3-2. 로그인 API 함수 추가

백엔드가 `application/x-www-form-urlencoded` 형식을 요구하므로 `URLSearchParams`를 사용하여 데이터를 변환합니다.

```typescript
/**
 * 로그인 API 호출
 * @param data 로그인 폼 데이터
 * @returns 로그인 결과
 */
export const Login = async (
  data: LoginRequest
): Promise<LoginResponse> => {
  // application/x-www-form-urlencoded 형식으로 데이터 변환
  const formData = new URLSearchParams();
  formData.append("username", data.username);
  formData.append("password", data.password);
  
  const response = await apiClient.post<LoginResponse>(
    "/auth/login",
    formData.toString(),
    {
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
    }
  );

  return response.data;
};
```

**주의사항**: 백엔드가 JSON 형식을 요구하는 경우, 위 코드 대신 아래와 같이 사용합니다:

```typescript
// JSON 형식 (일반적)
const response = await apiClient.post<LoginResponse>("/auth/login", {
  username: data.username,
  password: data.password,
});
```

### 3-3. 에러 메시지 변환 함수 추가

타입 캐스팅 없이 간단하게 접근합니다.

```typescript
/**
 * API 에러 코드를 사용자 친화적인 메시지로 변환
 * @param errorCode API 에러 코드
 * @param defaultMessage 기본 에러 메시지
 * @returns 사용자 친화적인 에러 메시지
 */
export const GetErrorMessage = (
  errorCode?: string,
  defaultMessage: string = "로그인에 실패했습니다."
): string => {
  if (!errorCode) return defaultMessage;

  return ERROR_MAPPING[errorCode] || defaultMessage;
};
```

### ✅ 완성된 파일 예시

`src/api/login/index.ts`의 전체 코드:

```typescript
import { apiClient } from "../axios";  // axios 기반 API 클라이언트 (baseURL, 인터셉터 포함)

// 로그인 요청 타입
export interface LoginRequest {
  username: string;
  password: string;
}

// 토큰 정보 타입
export interface TokenInfo {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

// 사용자 정보 타입
export interface UserInfo {
  id: number;
  username: string;
  name: string;
  role: string;
}

// 로그인 성공 응답 타입
export interface LoginSuccessResponse {
  status: "SUCCESS";
  data: {
    user: UserInfo;
    token: TokenInfo;
  };
}

// 로그인 실패 응답 타입
export interface LoginErrorResponse {
  status: "FAIL";
  error: {
    code: string;
    message: string;
  };
}

// 로그인 응답 타입
export type LoginResponse = LoginSuccessResponse | LoginErrorResponse;

// 에러 매핑 테이블
const ERROR_MAPPING: Record<string, string> = {
  INVALID_CREDENTIALS: "아이디 또는 비밀번호가 올바르지 않습니다.",
};

/**
 * 로그인 API 호출
 * @param data 로그인 폼 데이터
 * @returns 로그인 결과
 */
export const Login = async (
  data: LoginRequest
): Promise<LoginResponse> => {
  // application/x-www-form-urlencoded 형식으로 데이터 변환
  const formData = new URLSearchParams();
  formData.append("username", data.username);
  formData.append("password", data.password);
  
  const response = await apiClient.post<LoginResponse>(
    "/auth/login",
    formData.toString(),
    {
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
    }
  );

  return response.data;
};

/**
 * API 에러 코드를 사용자 친화적인 메시지로 변환
 * @param errorCode API 에러 코드
 * @param defaultMessage 기본 에러 메시지
 * @returns 사용자 친화적인 에러 메시지
 */
export const GetErrorMessage = (
  errorCode?: string,
  defaultMessage: string = "로그인에 실패했습니다."
): string => {
  if (!errorCode) return defaultMessage;

  return ERROR_MAPPING[errorCode] || defaultMessage;
};
```

---

## 4. Hook 생성

### 목표
로그인 로직을 관리하는 커스텀 Hook을 생성합니다.

### 작업 파일
**생성**: `src/hooks/login/index.ts`

### 4-1. 필요한 Import 추가

각 라이브러리의 용도를 명확히 하기 위해 주석을 추가합니다.

```typescript
import { useState } from "react";              // 로딩 상태 및 에러 상태 관리
import { useForm } from "react-hook-form";     // 폼 상태 관리 및 유효성 검사
import { zodResolver } from "@hookform/resolvers/zod";  // Zod 스키마를 react-hook-form과 연결
import * as z from "zod";                     // 유효성 검사 스키마 정의
import { useNavigate } from "react-router-dom";  // 페이지 이동 (로그인 성공 시 리다이렉트)
import { toast } from "sonner";               // 성공/실패 알림 메시지 표시
import { Login, GetErrorMessage } from "@/api/login";  // 로그인 API 호출 및 에러 처리
```

### 4-2-1. Zod란?

**Zod**는 TypeScript 기반의 런타임 타입 검증 라이브러리입니다.

#### 주요 특징
- **타입 안전성**: 스키마에서 TypeScript 타입을 자동으로 추론
- **런타임 검증**: 실행 시점에 데이터 유효성 검사
- **에러 메시지**: 커스텀 에러 메시지 제공
- **간단한 문법**: 직관적이고 읽기 쉬운 API

#### 기본 사용법
```typescript
import * as z from "zod";

// 문자열 검증
z.string().email("이메일 형식이 아닙니다");
z.string().min(8, "최소 8자 이상입니다");

// 숫자 검증
z.number().min(0, "0 이상이어야 합니다");

// 객체 검증
z.object({
  name: z.string(),
  age: z.number(),
});

// 타입 추론
type SchemaType = z.infer<typeof schema>;
```

#### 왜 사용하나요?
- 사용자 입력값 검증
- API 응답 데이터 검증
- 폼 제출 전 데이터 검증
- 타입 안전한 데이터 처리

---

### 4-2-2. Zod 유효성 검사 스키마 정의

로그인 폼에 필요한 검증 규칙을 정의합니다.

```typescript
// Zod 유효성 검사 스키마
const loginSchema = z.object({
  username: z.string().email("유효한 이메일 형식이 아닙니다."),
  password: z.string().min(1, "비밀번호를 입력해주세요."),
});

export type LoginFormValues = z.infer<typeof loginSchema>;
```

**설명**:
- `z.object()`: 객체 형태의 스키마 정의
- `z.string().email()`: 문자열이 이메일 형식인지 검증
- `z.string().min(1)`: 최소 1자 이상인지 검증
- `z.infer<typeof loginSchema>`: 스키마에서 TypeScript 타입 자동 추론

### 4-3. Hook 인터페이스 정의

```typescript=8:11
interface UseLoginProps {
  onLogin?: () => void;
}
```

### 4-4. Hook 함수 구현

```typescript
export const useLogin = ({ onLogin }: UseLoginProps = {}) => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  const form = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      username: "",
      password: "",
    },
  });

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = form;

  const onSubmit = async (data: LoginFormValues) => {
    setIsLoading(true);
    setApiError(null);

    try {
      const result = await Login({
        username: data.username,
        password: data.password,
      });

      if (result.status === "SUCCESS") {
        // 토큰 저장 (다음 단계에서 구현)
        const { access_token, refresh_token } = result.data.token;
        localStorage.setItem("access_token", access_token);
        localStorage.setItem("refresh_token", refresh_token);
        
        // 사용자 정보 저장
        localStorage.setItem("user", JSON.stringify(result.data.user));
        
        toast.success("로그인에 성공했습니다!");
        onLogin?.();
        navigate("/");
      } else {
        const errorMessage =
          GetErrorMessage(result.error?.code, result.error?.message) ||
          "로그인에 실패했습니다.";
        setApiError(errorMessage);
      }
    } catch {
      setApiError("네트워크 오류가 발생했습니다. 다시 시도해주세요.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleMode = () => {
    navigate("/signup");
  };

  return {
    form,
    register,
    handleSubmit,
    errors,
    isLoading,
    apiError,
    onSubmit,
    handleToggleMode,
  };
};
```

### ✅ 완성된 Hook 파일 예시

`src/hooks/login/index.ts`의 전체 코드는 위의 단계들을 합친 것입니다.

---

## 5. UI 컴포넌트 분리 및 수정

### 목표
회원가입 페이지와 동일한 구조로 컴포넌트를 분리하여 재사용성을 높입니다.

### 작업 파일
- `src/pages/login/components/ApiErrorDisplay.tsx` (생성)
- `src/pages/login/components/LoginForm.tsx` (생성)
- `src/pages/login/components/LoginFooter.tsx` (생성)
- `src/pages/login/index.tsx` (수정)

### 5-1. 컴포넌트 폴더 생성

터미널에서 다음 명령어를 실행합니다:

```bash
mkdir -p src/pages/login/components
```

### 5-2. ApiErrorDisplay 컴포넌트 생성

API 에러 메시지를 표시하는 컴포넌트입니다.

**파일**: `src/pages/login/components/ApiErrorDisplay.tsx`

```typescript
interface ApiErrorDisplayProps {
  error: string | null;
}

export const ApiErrorDisplay = ({ error }: ApiErrorDisplayProps) =>
  error ? (
    <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
      <div className="text-red-700 font-medium text-xl">{error}</div>
    </div>
  ) : null;
```

### 5-3. LoginForm 컴포넌트 생성

로그인 폼 필드들을 담은 컴포넌트입니다.

**파일**: `src/pages/login/components/LoginForm.tsx`

```typescript
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { LoginFormValues } from "@/hooks/login";
import type { UseFormRegister, UseFormHandleSubmit, FieldErrors } from "react-hook-form";

interface LoginFormProps {
  register: UseFormRegister<LoginFormValues>;
  handleSubmit: UseFormHandleSubmit<LoginFormValues>;
  errors: FieldErrors<LoginFormValues>;
  isLoading: boolean;
  onSubmit: (data: LoginFormValues) => void;
}

export const LoginForm = ({
  register,
  handleSubmit,
  errors,
  isLoading,
  onSubmit,
}: LoginFormProps) => {
  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
      {/* 이메일 필드 */}
      <div className="space-y-3">
        <label
          htmlFor="email"
          className="text-2xl font-semibold text-slate-800 md:text-3xl"
        >
          이메일
        </label>
        <input
          type="email"
          id="email"
          placeholder="이메일을 입력하세요"
          {...register("username")}
          disabled={isLoading}
          className={cn(
            "w-full h-16 rounded-xl border-2 text-xl font-semibold md:text-3xl placeholder:text-slate-300 px-4",
            errors.username ? "border-red-500" : "border-slate-200"
          )}
        />
        {errors.username && (
          <p className="text-xl font-semibold text-red-500">
            {errors.username.message}
          </p>
        )}
      </div>

      {/* 비밀번호 필드 */}
      <div className="space-y-3">
        <label
          htmlFor="password"
          className="text-2xl font-semibold text-slate-800 md:text-3xl"
        >
          비밀번호
        </label>
        <input
          type="password"
          id="password"
          placeholder="비밀번호를 입력하세요"
          {...register("password")}
          disabled={isLoading}
          className={cn(
            "w-full h-16 rounded-xl border-2 text-xl font-semibold md:text-3xl placeholder:text-slate-300 px-4",
            errors.password ? "border-red-500" : "border-slate-200"
          )}
        />
        {errors.password && (
          <p className="text-xl font-semibold text-red-500">
            {errors.password.message}
          </p>
        )}
      </div>

      {/* 로그인 버튼 */}
      <Button
        type="submit"
        disabled={isLoading}
        className="w-full h-auto py-4 bg-green-500 text-white hover:bg-green-600 rounded-xl text-2xl font-semibold md:text-3xl"
      >
        {isLoading ? "로그인 중..." : "로그인"}
      </Button>
    </form>
  );
};
```

### 5-4. LoginFooter 컴포넌트 생성

회원가입 링크를 표시하는 컴포넌트입니다.

**파일**: `src/pages/login/components/LoginFooter.tsx`

```typescript
import { Button } from "@/components/ui/button";

interface LoginFooterProps {
  onToggleMode: () => void;
  isLoading: boolean;
}

export const LoginFooter = ({ onToggleMode, isLoading }: LoginFooterProps) => (
  <>
    <p className="text-lg font-semibold text-slate-500 md:text-2xl">
      회원이 아니신가요?&nbsp;
    </p>
    <Button
      variant="link"
      onClick={onToggleMode}
      disabled={isLoading}
      className="p-0 text-lg font-semibold text-blue-600 md:text-2xl"
    >
      회원가입
    </Button>
  </>
);
```

### 5-5. 메인 페이지 수정

컴포넌트를 사용하도록 메인 페이지를 수정합니다.

**파일**: `src/pages/login/index.tsx`

```typescript
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useLogin } from "@/hooks/login";
import { ApiErrorDisplay } from "./components/ApiErrorDisplay";
import { LoginForm } from "./components/LoginForm";
import { LoginFooter } from "./components/LoginFooter";

interface LoginPageProps {
  onLogin: () => void;
}

const LoginPage: React.FC<LoginPageProps> = ({ onLogin }) => {
  const {
    register,
    handleSubmit,
    errors,
    isLoading,
    apiError,
    onSubmit,
    handleToggleMode,
  } = useLogin({ onLogin });

  return (
    <div className="w-full flex justify-center items-center py-12 px-4">
      <Card className="w-full max-w-2xl">
        <CardHeader>
          <CardTitle className="text-center text-4xl font-extrabold md:text-5xl text-slate-800 py-6">
            로그인
          </CardTitle>
        </CardHeader>
        <CardContent className="pb-0">
          <ApiErrorDisplay error={apiError} />
          <LoginForm
            register={register}
            handleSubmit={handleSubmit}
            errors={errors}
            isLoading={isLoading}
            onSubmit={onSubmit}
          />
        </CardContent>
        <CardFooter className="flex-col sm:flex-row justify-center items-baseline pt-8">
          <LoginFooter onToggleMode={handleToggleMode} isLoading={isLoading} />
        </CardFooter>
      </Card>
    </div>
  );
};

export default LoginPage;
```

### ✅ 체크리스트
- [ ] 컴포넌트 폴더 생성 완료
- [ ] ApiErrorDisplay 컴포넌트 생성 완료
- [ ] LoginForm 컴포넌트 생성 완료
- [ ] LoginFooter 컴포넌트 생성 완료
- [ ] 메인 페이지 수정 완료
- [ ] 모든 컴포넌트 정상 작동 확인

---

## 6. 토큰 저장 기능 추가

### 목표
로그인 성공 시 토큰을 localStorage에 저장하고, API 요청 시 자동으로 토큰을 포함하도록 설정합니다.

### 작업 파일
`src/api/axios.ts`

### 6-1. Axios 요청 인터셉터 수정

```typescript
// 요청 인터셉터
apiClient.interceptors.request.use(
  (config) => {
    // localStorage에서 토큰 가져오기
    const token = localStorage.getItem("access_token");
    
    // 토큰이 있으면 Authorization 헤더에 추가
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);
```

### 6-2. Axios 응답 인터셉터 추가 (토큰 만료 처리)

```typescript
// 응답 인터셉터
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    // 401 에러 발생 시 (토큰 만료)
    if (error.response?.status === 401) {
      const refreshToken = localStorage.getItem("refresh_token");
      
      if (refreshToken) {
        try {
          // Refresh Token으로 새로운 Access Token 받기
          const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          
          const { access_token } = response.data.data.token;
          localStorage.setItem("access_token", access_token);
          
          // 원래 요청 재시도
          error.config.headers.Authorization = `Bearer ${access_token}`;
          return apiClient.request(error.config);
        } catch {
          // Refresh Token도 만료된 경우 로그아웃 처리
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          localStorage.removeItem("user");
          window.location.href = "/login";
        }
      }
    }
    
    return Promise.reject(error);
  }
);
```

---

## 7. 테스트

### 목표
로그인 기능이 올바르게 작동하는지 확인합니다.

### 7-1. 린터 실행

```bash
npm run lint
```

### 7-2. 개발 서버 실행

```bash
npm run dev
```

### 7-3. 기능 테스트

#### 테스트 1: 이메일 형식 검증
- **입력**: `invalid-email`
- **예상 결과**: "유효한 이메일 형식이 아닙니다." 에러 메시지 표시

#### 테스트 2: 빈 비밀번호
- **입력**: 이메일만 입력, 비밀번호 빈칸
- **예상 결과**: "비밀번호를 입력해주세요." 에러 메시지 표시

#### 테스트 3: 잘못된 로그인 정보
- **입력**: 존재하지 않는 이메일/비밀번호
- **예상 결과**: "아이디 또는 비밀번호가 올바르지 않습니다." 에러 메시지 표시

#### 테스트 4: 올바른 로그인 정보
- **입력**: 등록된 이메일/비밀번호
- **예상 결과**: 
  - 토큰이 localStorage에 저장됨
  - 사용자 정보가 localStorage에 저장됨
  - 토스트 알림 표시
  - 홈페이지로 리다이렉트

### ✅ 체크리스트
- [ ] 린터 에러 없음
- [ ] 개발 서버 정상 실행
- [ ] 이메일 형식 검증 작동
- [ ] 비밀번호 필수 검증 작동
- [ ] 잘못된 정보 시 에러 메시지 표시
- [ ] 올바른 정보 시 로그인 성공
lsa
- [ ] 토큰 저장 확인
- [ ] 홈페이지 리다이렉트 확인

---

## 완료!

축하합니다! 로그인 API 연결이 완료되었습니다. 🎉

### 최종 결과

이제 로그인 페이지에서:
- ✅ 이메일/비밀번호 입력 및 유효성 검사
- ✅ API 호출을 통한 로그인 처리
- ✅ 토큰 자동 저장 및 관리
- ✅ 에러 처리 및 사용자 피드백
- ✅ 로그인 성공 시 홈페이지 리다이렉트

### 변경된 파일 목록

```
✅ src/api/login/index.ts              - 로그인 API 함수 생성
✅ src/hooks/login/index.ts            - 로그인 Hook 생성
✅ src/pages/login/index.tsx           - UI 수정
✅ src/api/axios.ts                    - 토큰 인터셉터 추가
```

### 다음 단계 (선택)

1. **로그아웃 기능**: localStorage에서 토큰 제거 및 로그인 페이지로 리다이렉트
2. **자동 로그인**: 페이지 새로고침 시 토큰 확인하여 자동 로그인 상태 유지
3. **프로필 페이지**: 사용자 정보 표시 및 수정 기능

---

## 문제 해결

### 에러: `Login is not defined`
- **원인**: `src/hooks/login/index.ts`에서 import 누락
- **해결**: `import { Login, GetErrorMessage } from "@/api/login";` 확인

### 에러: `useLogin is not defined`
- **원인**: `src/pages/login/index.tsx`에서 import 누락
- **해결**: `import { useLogin } from '@/hooks/login';` 확인

### 토큰이 저장되지 않음
- **원인**: 로그인 성공 시 토큰 저장 코드 미구현
- **해결**: `onSubmit` 함수에서 `localStorage.setItem` 확인

---

## 참고 자료

- [React Hook Form 공식 문서](https://react-hook-form.com/)
- [Axios 공식 문서](https://axios-http.com/)
- [Zod 공식 문서](https://zod.dev/)

