import { apiClient } from "../axios";

// 회원가입 API 타입 정의
export interface SignupRequest {
  username: string;
  password: string;
  name: string;
  phone_number: string;
  gender: "MALE" | "FEMALE";
}

export interface SignupResponse {
  status: "SUCCESS" | "FAILURE";
  error?: {
    code: string;
    message: string;
  };
}

// 에러 매핑 테이블
const ERROR_MAPPING = {
  USERNAME_ALREADY_EXISTS: "이미 등록된 이메일입니다.",
  INVALID_PHONE_NUMBER: "올바른 전화번호를 입력해주세요.",
  INVALID_GENDER: "성별을 선택해주세요.",
} as const;

/**
 * 회원가입 API 호출
 * @param data 회원가입 폼 데이터
 * @returns 회원가입 결과
 */
export const signup = async (
  data: SignupRequest
): Promise<SignupResponse> => {
  const response = await apiClient.post<SignupResponse>("/auth/signup", {
    username: data.username,
    password: data.password,
    name: data.name,
    phone_number: data.phone_number,
    gender: data.gender,
  });

  return response.data;
};

/**
 * API 에러 코드를 사용자 친화적인 메시지로 변환
 * @param errorCode API 에러 코드
 * @param defaultMessage 기본 에러 메시지
 * @returns 사용자 친화적인 에러 메시지
 */
export const getErrorMessage = (
  errorCode?: string,
  defaultMessage: string = "회원가입에 실패했습니다."
): string => {
  if (!errorCode) return defaultMessage;
  
  return (
    ERROR_MAPPING[errorCode as keyof typeof ERROR_MAPPING] ||
    defaultMessage
  );
};

