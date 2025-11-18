import { Button } from "@/shared/components/ui/button";
import { cn } from "@/shared/utils/cn";
import type { LoginFormValues } from "@features/auth/hooks/useLogin";
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

