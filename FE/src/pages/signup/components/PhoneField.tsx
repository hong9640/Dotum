import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { ErrorMessage } from "./ErrorMessage";
import { cn } from "@/lib/utils";

interface PhoneFieldProps {
  phoneValue: string;
  formatPhoneDisplay: (value: string) => string;
  onPhoneChange: (value: string) => void;
  error?: string;
  disabled?: boolean;
}

export const PhoneField = ({
  phoneValue,
  formatPhoneDisplay,
  onPhoneChange,
  error,
  disabled,
}: PhoneFieldProps) => (
  <div className="space-y-3">
    <Label
      htmlFor="phone_number"
      className="text-2xl font-semibold text-slate-800 md:text-3xl"
    >
      전화번호
    </Label>
    <Input
      type="tel"
      id="phone_number"
      placeholder="010-1234-5678"
      value={formatPhoneDisplay(phoneValue)}
      onChange={(e) => {
        const numbers = e.target.value.replace(/\D/g, "");
        onPhoneChange(numbers);
      }}
      disabled={disabled}
      aria-invalid={error ? "true" : "false"}
      aria-describedby={error ? "phone-error" : undefined}
      className={cn(
        "h-16 rounded-xl border-2 text-xl font-normal md:text-3xl placeholder:text-slate-300 px-6",
        error ? "border-red-500" : "border-slate-200"
      )}
    />
    <ErrorMessage message={error} id="phone-error" />
  </div>
);

