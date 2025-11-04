import { EmailVerificationField } from "./EmailVerificationField";
import { FormField } from "./FormField";
import { Button } from "@/components/ui/button";
import type { SignupFormValues } from "@/hooks/signup";
import type { UseFormRegister, UseFormHandleSubmit, FieldErrors } from "react-hook-form";

interface SignupFormProps {
  register: UseFormRegister<SignupFormValues>;
  handleSubmit: UseFormHandleSubmit<SignupFormValues>;
  errors: FieldErrors<SignupFormValues>;
  isLoading: boolean;
  onSubmit: (data: SignupFormValues) => void;
  onEmailVerification: () => void;
  emailVerificationStatus?: string | null;
}

export const SignupForm = ({
  register,
  handleSubmit,
  errors,
  isLoading,
  onSubmit,
  onEmailVerification,
  emailVerificationStatus,
}: SignupFormProps) => {

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
      <EmailVerificationField
        register={register}
        error={errors.username?.message}
        disabled={isLoading}
        onVerify={onEmailVerification}
        verificationStatus={emailVerificationStatus}
      />

      <FormField
        id="password"
        label="비밀번호"
        type="password"
        placeholder="비밀번호를 입력하세요"
        register={register}
        error={errors.password?.message}
        disabled={isLoading}
      />

      <FormField
        id="confirmPassword"
        label="비밀번호 확인"
        type="password"
        placeholder="비밀번호를 입력하세요"
        register={register}
        error={errors.confirmPassword?.message}
        disabled={isLoading}
      />

      <Button
        type="submit"
        disabled={isLoading}
        size="lg"
        className="w-full bg-green-500 hover:bg-green-600"
      >
        {isLoading ? "가입 중..." : "회원가입"}
      </Button>
    </form>
  );
};

