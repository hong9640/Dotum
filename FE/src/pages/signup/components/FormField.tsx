import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { cn } from "@/utils/cn";
import type { SignupFormValues } from "@/hooks/signup";
import type { UseFormRegister } from "react-hook-form";

interface FormFieldProps {
  id: keyof SignupFormValues;
  label: string;
  type: string;
  placeholder: string;
  register: UseFormRegister<SignupFormValues>;
  error?: string;
  disabled?: boolean;
}

export const FormField = ({
  id,
  label,
  type,
  placeholder,
  register,
  error,
  disabled,
}: FormFieldProps) => (
  <div className="space-y-3">
    <Label className="text-2xl md:text-3xl font-semibold">
      {label}
    </Label>
    <Input
      type={type}
      placeholder={placeholder}
      {...register(id)}
      disabled={disabled}
      className={cn(
        "text-xl md:text-3xl h-16",
        error && "border-red-500"
      )}
    />
    {error && (
      <p className="text-xl font-semibold text-red-500">{error}</p>
    )}
  </div>
);

