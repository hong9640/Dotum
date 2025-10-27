import { Button } from "@/components/ui/button";

interface SignupFooterProps {
  onToggleMode: () => void;
  isLoading: boolean;
}

export const SignupFooter = ({ onToggleMode, isLoading }: SignupFooterProps) => (
  <>
    <p className="text-lg font-semibold text-slate-500 md:text-2xl">
      이미 계정이 있으신가요?&nbsp;
    </p>
    <Button
      variant="link"
      onClick={onToggleMode}
      disabled={isLoading}
      className="p-0 text-lg font-semibold text-blue-600 md:text-2xl"
    >
      로그인
    </Button>
  </>
);

