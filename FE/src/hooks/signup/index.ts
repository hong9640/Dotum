import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { signup, getErrorMessage } from "@/api/signup";

// Zod 유효성 검사 스키마
const signupSchema = z
  .object({
    username: z.string().email("유효한 이메일 형식이 아닙니다."),
    password: z.string().min(8, "비밀번호는 8자 이상이어야 합니다."),
    confirmPassword: z.string(),
    name: z.string().min(1, "이름을 입력해주세요."),
    phone_number: z.string().min(1, "전화번호를 입력해주세요."),
    gender: z.enum(["MALE", "FEMALE"], { message: "성별을 선택해주세요." }),
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

  const form = useForm<SignupFormValues>({
    resolver: zodResolver(signupSchema),
    defaultValues: {
      username: "",
      password: "",
      confirmPassword: "",
      name: "",
      phone_number: "",
      gender: undefined,
    },
  });

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
    setValue,
  } = form;

  // 전화번호 포맷팅 함수
  const formatPhoneDisplay = (value: string) => {
    const numbers = value.replace(/\D/g, "");
    if (numbers.length <= 3) return numbers;
    if (numbers.length <= 7)
      return `${numbers.slice(0, 3)}-${numbers.slice(3)}`;
    return `${numbers.slice(0, 3)}-${numbers.slice(3, 7)}-${numbers.slice(
      7,
      11
    )}`;
  };

  const phoneValue = watch("phone_number") || "";

  const onSubmit = async (data: SignupFormValues) => {
    setIsLoading(true);
    setApiError(null);

    try {
      const result = await signup({
        username: data.username,
        password: data.password,
        name: data.name,
        phone_number: data.phone_number,
        gender: data.gender,
      });

      if (result.status === "SUCCESS") {
        toast.success("회원가입이 완료되었습니다!");
        onSignup?.();
        navigate("/login");
      } else {
        const errorMessage =
          getErrorMessage(result.error?.code, result.error?.message) ||
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

  return {
    form,
    register,
    handleSubmit,
    errors,
    watch,
    setValue,
    isLoading,
    apiError,
    phoneValue,
    formatPhoneDisplay,
    onSubmit,
    handleToggleMode,
  };
};

