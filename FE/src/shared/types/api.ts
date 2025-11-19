// API 공통 응답 타입

// 에러 상세 정보
export interface ErrorDetail {
  code: string;
  message: string;
}

// 실패 응답 (백엔드 FailResponse)
export interface FailResponse {
  status: "FAIL";
  error: ErrorDetail;
}

// === Auth 관련 타입 ===

// 로그인 요청
export interface LoginRequest {
  username: string; // 이메일
  password: string;
}

// 사용자 정보
export interface UserInfo {
  user_id: number;
  username: string; // 이메일
  name: string;
  role: string;
}

// 토큰 정보
export interface TokenInfo {
  access_token: string;
  token_type: string;
  expires_in: number;
}

// 로그인 성공 데이터
export interface LoginSuccessData {
  user: UserInfo;
  token: TokenInfo;
}

// 로그인 성공 응답
export interface LoginSuccessResponse {
  status: "SUCCESS";
  data: LoginSuccessData;
}

// 로그인 응답 (성공 또는 실패)
export type LoginResponse = LoginSuccessResponse | FailResponse;

// 회원가입 요청
export interface SignupRequest {
  username: string; // 이메일
  password: string;
  name: string;
}

// 회원가입 성공 사용자 정보
export interface SignupSuccessUser {
  user_id: number;
  username: string;
  name: string;
  role: string;
  created_at: string;
}

// 회원가입 성공 데이터
export interface SignupSuccessData {
  user: SignupSuccessUser;
}

// 회원가입 성공 응답
export interface SignupSuccessResponse {
  status: "SUCCESS";
  data: SignupSuccessData;
  message: string;
}

// 회원가입 응답
export type SignupResponse = SignupSuccessResponse | FailResponse;

// 이메일 중복 확인 정보
export interface VerifyInfo {
  email: string;
  is_duplicate: boolean;
  message: string;
}

// 이메일 중복 확인 응답
export interface EmailCheckResponse {
  status: string;
  data: VerifyInfo;
}

// 로그아웃 성공 응답
export interface LogoutSuccessResponse {
  status: "SUCCESS";
  message: string;
}

// 로그아웃 응답
export type LogoutResponse = LogoutSuccessResponse | FailResponse;

// === 에러 응답 타입 ===

// 에러 상세 (백엔드 ErrorDetail)
export interface ErrorDetailField {
  field?: string;
  message: string;
}

// 일반 에러 응답
export interface ErrorResponse {
  detail: string | ErrorDetailField[];
}

// Axios 에러 타입
export interface AxiosErrorResponse {
  response?: {
    status?: number;
    statusText?: string;
    data?: ErrorResponse & {
      error?: ErrorDetail;
      message?: string;
    };
  };
  message?: string;
  name?: string;
}

// 확장된 에러 타입 (status와 originalError 포함)
export class EnhancedError extends Error {
  status?: number;
  originalError?: unknown;

  constructor(message: string, status?: number, originalError?: unknown) {
    super(message);
    this.name = 'EnhancedError';
    this.status = status;
    this.originalError = originalError;
    
    // TypeScript의 프로토타입 체인 유지
    Object.setPrototypeOf(this, EnhancedError.prototype);
  }
}

