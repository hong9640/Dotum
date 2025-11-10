import { useState, useEffect, useRef } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Signup, CheckEmailDuplication } from "@/api/signup";
import { useAlertDialog } from "@/hooks/useAlertDialog";
import type { AxiosErrorResponse } from "@/types/api";

// Zod 유효성 검사 스키마
const signupSchema = z
  .object({
    username: z.string().email("유효한 이메일 형식이 아닙니다."),
    password: z.string().min(8, "비밀번호는 8자 이상이어야 합니다."),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "비밀번호가 일치하지 않습니다.",
    path: ["confirmPassword"],
  });

export type SignupFormValues = z.infer<typeof signupSchema>;

interface UseSignupProps {
  onSignup?: () => void;
}

export const useSignup = ({ onSignup }: UseSignupProps = {}) => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [isEmailVerified, setIsEmailVerified] = useState(false);
  const [emailVerificationStatus, setEmailVerificationStatus] = useState<string | null>(null);
  const { showAlert, AlertDialog } = useAlertDialog();

  const form = useForm<SignupFormValues>({
    resolver: zodResolver(signupSchema),
    mode: "onChange", // 실시간 검증
    defaultValues: {
      username: "",
      password: "",
      confirmPassword: "",
    },
  });

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
  } = form;

  const emailValue = watch("username") || "";
  const prevEmailRef = useRef<string>("");
  
  // 이메일 값이 실제로 변경되면 중복 확인 상태 리셋
  useEffect(() => {
    if (emailValue !== prevEmailRef.current) {
      if (isEmailVerified) {
        setIsEmailVerified(false);
        setEmailVerificationStatus(null);
      }
      prevEmailRef.current = emailValue;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [emailValue]);

  // 이메일 인증 체크 함수 (AlertDialog 표시)
  const checkEmailVerification = () => {
    showAlert({
      title: "이메일 인증이 필요합니다",
      description: "회원가입을 진행하려면 먼저 이메일 중복 확인을 완료해주세요.",
    });
  };

  const onSubmit = async (data: SignupFormValues) => {
    setIsLoading(true);
    setApiError(null);

    try {
      const result = await Signup({
        username: data.username,
        password: data.password,
      });

      if (result.status === "SUCCESS") {
        toast.success("회원가입이 완료되었습니다!");
        onSignup?.();
        navigate("/login");
      } else {
        // 서버에서 온 메시지만 사용
        const errorMessage = result.error?.message || "";
        if (errorMessage) {
          setApiError(errorMessage);
        }
      }
    } catch (error: unknown) {
      // 네트워크 에러 등 예외 상황
      console.error("회원가입 에러:", error);
      // 서버 응답이 있으면 사용, 없으면 빈 문자열
      const axiosError = error as AxiosErrorResponse;
      const errorMessage = axiosError.response?.data?.error?.message || 
                          axiosError.response?.data?.message || "";
      if (errorMessage) {
        setApiError(errorMessage);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleMode = () => {
    navigate("/login");
  };

  const handleEmailVerification = async () => {
    if (!emailValue) {
      setEmailVerificationStatus("이메일을 입력해주세요.");
      setIsEmailVerified(false);
      return;
    }

    try {
      const result = await CheckEmailDuplication(emailValue);
      
      // SUCCESS 상태이고 중복이 아닌 경우
      if (result.status === "SUCCESS" && result.data?.is_duplicate === false) {
        setIsEmailVerified(true);
        setEmailVerificationStatus("사용 가능한 이메일입니다.");
      } else {
        // 중복이거나 다른 에러
        setIsEmailVerified(false);
        const errorMessage = result.data?.message || "이메일 확인에 실패했습니다.";
        setEmailVerificationStatus(errorMessage);
      }
    } catch (error: unknown) {
      // 네트워크 에러 등 예외 상황
      console.error("이메일 확인 에러:", error);
      setIsEmailVerified(false);
      
      const axiosError = error as AxiosErrorResponse;
      const errorMessage = axiosError.response?.data?.error?.message || 
                          axiosError.response?.data?.message || 
                          "이메일 확인 중 오류가 발생했습니다.";
      setEmailVerificationStatus(errorMessage);
    }
  };

  return {
    form,
    register,
    handleSubmit,
    errors,
    isLoading,
    apiError,
    emailValue,
    isEmailVerified,
    emailVerificationStatus,
    onSubmit,
    handleToggleMode,
    handleEmailVerification,
    checkEmailVerification,
    AlertDialog,
  };
};

