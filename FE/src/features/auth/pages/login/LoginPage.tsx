import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/shared/components/ui/card";
import { useLogin } from "@features/auth/hooks/useLogin";
import { ApiErrorDisplay } from "./components/ApiErrorDisplay";
import { LoginForm } from "./components/LoginForm";
import { LoginFooter } from "./components/LoginFooter";

interface LoginPageProps {
  onLogin: () => void;
}

const LoginPage: React.FC<LoginPageProps> = ({ onLogin }) => {
  const {
    register,
    handleSubmit,
    errors,
    isLoading,
    apiError,
    onSubmit,
    handleToggleMode,
  } = useLogin({ onLogin });

  return (
    <div className="w-full flex justify-center items-center py-12 px-4">
      <Card className="w-full max-w-2xl">
        <CardHeader>
          <CardTitle className="text-center text-4xl font-extrabold md:text-5xl text-slate-800 py-6">
            로그인
          </CardTitle>
        </CardHeader>
        <CardContent className="pb-0">
          <ApiErrorDisplay error={apiError} />
          <LoginForm
            register={register}
            handleSubmit={handleSubmit}
            errors={errors}
            isLoading={isLoading}
            onSubmit={onSubmit}
          />
        </CardContent>
        <CardFooter className="flex-col sm:flex-row justify-center items-baseline pt-8">
          <LoginFooter onToggleMode={handleToggleMode} isLoading={isLoading} />
        </CardFooter>
      </Card>
    </div>
  );
};

export default LoginPage;
