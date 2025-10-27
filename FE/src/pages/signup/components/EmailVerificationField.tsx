import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { SignupFormValues } from "@/hooks/signup";
import type { UseFormRegister } from "react-hook-form";

interface EmailVerificationFieldProps {
  register: UseFormRegister<SignupFormValues>;
  error?: string;
  disabled?: boolean;
  onVerify?: () => void;
  verificationStatus?: string | null;
}

export const EmailVerificationField = ({
  register,
  error,
  disabled,
  onVerify,
  verificationStatus,
}: EmailVerificationFieldProps) => (
  <div className="space-y-3">
    <Label className="text-2xl md:text-3xl font-semibold">
      이메일
    </Label>
    <div className="flex gap-3">
      <Input
        type="email"
        placeholder="이메일을 입력하세요"
        {...register("username")}
        disabled={disabled}
        className={cn(
          "flex-1 text-xl md:text-3xl h-16",
          error && "border-red-500"
        )}
      />
      <Button
        type="button"
        onClick={onVerify}
        disabled={disabled}
        size="lg"
        className="bg-green-500 hover:bg-green-600 min-w-[200px]"
      >
        인증
      </Button>
    </div>
    {error && (
      <p className="text-xl font-semibold text-red-500">{error}</p>
    )}
    {verificationStatus && !error && (
      <p className={cn(
        "text-xl font-semibold",
        verificationStatus.includes("사용 가능") ? "text-green-500" : "text-red-500"
      )}>
        {verificationStatus}
      </p>
    )}
  </div>
);

