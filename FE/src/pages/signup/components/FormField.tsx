import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { ErrorMessage } from "./ErrorMessage";
import { cn } from "@/lib/utils";
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
    <Label
      htmlFor={id}
      className="text-2xl font-semibold text-slate-800 md:text-3xl"
    >
      {label}
    </Label>
    <Input
      type={type}
      id={id}
      placeholder={placeholder}
      {...register(id)}
      disabled={disabled}
      aria-invalid={error ? "true" : "false"}
      aria-describedby={error ? `${id}-error` : undefined}
      className={cn(
        "h-16 rounded-xl border-2 text-xl font-normal md:text-3xl placeholder:text-slate-300 px-6",
        error ? "border-red-500" : "border-slate-200"
      )}
    />
    <ErrorMessage message={error} id={`${id}-error`} />
  </div>
);

