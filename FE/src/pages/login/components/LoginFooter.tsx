import { Button } from "@/components/ui/button";

interface LoginFooterProps {
  onToggleMode: () => void;
  isLoading: boolean;
}

export const LoginFooter = ({ onToggleMode, isLoading }: LoginFooterProps) => (
  <>
    <p className="text-lg font-semibold text-slate-500 md:text-2xl">
      회원이 아니신가요?&nbsp;
    </p>
    <Button
      variant="link"
      onClick={onToggleMode}
      disabled={isLoading}
      className="p-0 text-lg font-semibold text-blue-600 md:text-2xl"
    >
      회원가입
    </Button>
  </>
);

