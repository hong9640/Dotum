import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useSignup } from "@/hooks/signup";
import { ApiErrorDisplay } from "./components/ApiErrorDisplay";
import { SignupForm } from "./components/SignupForm";
import { SignupFooter } from "./components/SignupFooter";

interface SignupPageProps {
  onSignup: () => void;
}

const SignupPage: React.FC<SignupPageProps> = ({ onSignup }) => {
  const {
    register,
    handleSubmit,
    errors,
    isLoading,
    apiError,
    onSubmit,
    handleToggleMode,
    handleEmailVerification,
    emailVerificationStatus,
  } = useSignup({ onSignup });

  return (
    <div className="w-full flex justify-center items-center py-12 px-4">
      <Card className="w-full max-w-2xl">
        <CardHeader>
          <CardTitle className="text-center text-4xl font-extrabold md:text-5xl text-slate-800 py-6">
            회원가입
          </CardTitle>
        </CardHeader>
        <CardContent className="pb-0">
          <ApiErrorDisplay error={apiError} />
          <SignupForm
            register={register}
            handleSubmit={handleSubmit}
            errors={errors}
            isLoading={isLoading}
            onSubmit={onSubmit}
            onEmailVerification={handleEmailVerification}
            emailVerificationStatus={emailVerificationStatus}
          />
        </CardContent>
        <CardFooter className="flex-col sm:flex-row justify-center items-baseline pt-8">
          <SignupFooter onToggleMode={handleToggleMode} isLoading={isLoading} />
        </CardFooter>
      </Card>
    </div>
  );
};

export default SignupPage;
