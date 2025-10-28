import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Signup, CheckEmailDuplication, GetErrorMessage } from "@/api/signup";

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

  const form = useForm<SignupFormValues>({
    resolver: zodResolver(signupSchema),
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
        const errorMessage =
          GetErrorMessage(result.error?.code, result.error?.message) ||
          "회원가입에 실패했습니다.";
        setApiError(errorMessage);
      }
    } catch {
      setApiError("네트워크 오류가 발생했습니다. 다시 시도해주세요.");
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
      return;
    }

    try {
      const result = await CheckEmailDuplication(emailValue);
      
      if (result.status === "SUCCESS" && !result.data.is_duplicate) {
        setIsEmailVerified(true);
        setEmailVerificationStatus("사용 가능한 이메일입니다.");
      } else {
        setIsEmailVerified(false);
        setEmailVerificationStatus("이미 등록된 이메일입니다.");
      }
    } catch {
      setEmailVerificationStatus("이메일 확인 중 오류가 발생했습니다.");
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
  };
};

