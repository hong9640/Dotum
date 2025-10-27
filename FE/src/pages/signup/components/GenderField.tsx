import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { ErrorMessage } from "./ErrorMessage";
import type { SignupFormValues } from "@/hooks/signup";
import type { UseFormRegister } from "react-hook-form";

interface GenderFieldProps {
  register: UseFormRegister<SignupFormValues>;
  error?: string;
  disabled?: boolean;
}

export const GenderField = ({ register, error, disabled }: GenderFieldProps) => (
  <div className="space-y-3">
    <Label className="text-2xl font-semibold text-slate-800 md:text-3xl">
      성별
    </Label>
    <RadioGroup
      {...register("gender")}
      disabled={disabled}
      aria-invalid={error ? "true" : "false"}
      aria-describedby={error ? "gender-error" : undefined}
      className="flex gap-6"
    >
      <div className="flex items-center space-x-2">
        <RadioGroupItem value="MALE" id="male" />
        <Label htmlFor="male" className="text-xl font-normal md:text-2xl">
          남성
        </Label>
      </div>
      <div className="flex items-center space-x-2">
        <RadioGroupItem value="FEMALE" id="female" />
        <Label htmlFor="female" className="text-xl font-normal md:text-2xl">
          여성
        </Label>
      </div>
    </RadioGroup>
    <ErrorMessage message={error} id="gender-error" />
  </div>
);

