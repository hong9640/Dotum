import { FormField } from "./FormField";
import { PhoneField } from "./PhoneField";
import { GenderField } from "./GenderField";
import { Button } from "@/components/ui/button";
import type { SignupFormValues } from "@/hooks/signup";
import type { UseFormRegister, UseFormHandleSubmit, FieldErrors, UseFormSetValue } from "react-hook-form";

interface SignupFormProps {
  register: UseFormRegister<SignupFormValues>;
  handleSubmit: UseFormHandleSubmit<SignupFormValues>;
  errors: FieldErrors<SignupFormValues>;
  setValue: UseFormSetValue<SignupFormValues>;
  isLoading: boolean;
  phoneValue: string;
  formatPhoneDisplay: (value: string) => string;
  onSubmit: (data: SignupFormValues) => void;
}

export const SignupForm = ({
  register,
  handleSubmit,
  errors,
  setValue,
  isLoading,
  phoneValue,
  formatPhoneDisplay,
  onSubmit,
}: SignupFormProps) => (
  <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
    <FormField
      id="username"
      label="이메일"
      type="email"
      placeholder="이메일을 입력하세요"
      register={register}
      error={errors.username?.message}
      disabled={isLoading}
    />

    <FormField
      id="name"
      label="이름"
      type="text"
      placeholder="이름을 입력하세요"
      register={register}
      error={errors.name?.message}
      disabled={isLoading}
    />

    <PhoneField
      phoneValue={phoneValue}
      formatPhoneDisplay={formatPhoneDisplay}
      onPhoneChange={(value) => setValue("phone_number", value)}
      error={errors.phone_number?.message}
      disabled={isLoading}
    />

    <GenderField
      register={register}
      error={errors.gender?.message}
      disabled={isLoading}
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
      className="w-full bg-green-500 hover:bg-green-600 text-white"
    >
      {isLoading ? "가입 중..." : "회원가입"}
    </Button>
  </form>
);

