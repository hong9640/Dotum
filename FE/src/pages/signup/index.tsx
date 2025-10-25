import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

// Zod 유효성 검사 스키마
const signupSchema = z
  .object({
    email: z.string().nonempty("필수 입력 항목입니다").email("유효한 이메일 형식이 아닙니다."),
    password: z.string().nonempty("필수 입력 항목입니다").min(8, "비밀번호는 8자 이상이어야 합니다."),
    confirmPassword: z.string().nonempty("필수 입력 항목입니다"),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "입력한 비밀번호와 다릅니다.",
    path: ["confirmPassword"],
  });

type SignupFormValues = z.infer<typeof signupSchema>;

interface SignupPageProps {
  onSignup: () => void;
}

const SignupPage: React.FC<SignupPageProps> = ({ onSignup }) => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);

  const form = useForm<SignupFormValues>({
    resolver: zodResolver(signupSchema),
    defaultValues: {
      email: '',
      password: '',
      confirmPassword: '',
    },
  });

  const { register, handleSubmit, formState: { errors } } = form;

  const onSubmit = async (data: SignupFormValues) => {
    setIsLoading(true);
    try {
      // 회원가입 로직 처리
      console.log('회원가입 시도:', data);
      
      // 회원가입 성공 시
      onSignup();
      navigate('/login'); // 로그인 페이지로 리다이렉트
    } catch (error) {
      console.error('회원가입 실패:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleMode = () => {
    navigate('/login');
  };

  // 에러 메시지 컴포넌트
  const ErrorMessage = ({ message }: { message?: string }) => (
    <>
    {message && (
    <div className="h-7 flex items-start">
      {message && (
        <div className="text-red-500 text-xl font-semibold">
          {message}
        </div>
      )}
    </div>
    )}
    </>
  );

  return (
    <div className="w-full flex justify-center items-center py-12 px-4">
      <Card className="w-full max-w-2xl">
        <CardHeader>
          <CardTitle className="text-center text-4xl font-extrabold md:text-5xl text-slate-800 py-6">
            회원가입
          </CardTitle>
        </CardHeader>
        <CardContent className="pb-0">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
            {/* 이메일 필드 */}
            <div className="space-y-3">
              <Label
                htmlFor="email"
                className="text-2xl font-semibold text-slate-800 md:text-3xl"
              >
                이메일
              </Label>
              <div className="flex gap-2">
                <div className="flex-1">
                  <Input
                    type="email"
                    id="email"
                    placeholder="이메일을 입력하세요"
                    {...register("email")}
                    disabled={isLoading}
                    className={`h-16 rounded-xl border-2 text-xl font-normal md:text-3xl placeholder:text-slate-300 px-6 ${
                      errors.email ? 'border-red-500' : 'border-slate-200'
                    }`}
                  />
                </div>
                <Button
                  type="button"
                  disabled={isLoading}
                  size="md"
                  className="w-40 bg-green-500 hover:bg-green-600 text-white"
                >
                  인증
                </Button>
              </div>
              <ErrorMessage message={errors.email?.message} />
            </div>

            {/* 비밀번호 필드 */}
            <div className="space-y-3">
              <Label
                htmlFor="password"
                className="text-2xl font-semibold text-slate-800 md:text-3xl"
              >
                비밀번호
              </Label>
              <Input
                type="password"
                id="password"
                placeholder="비밀번호를 입력하세요"
                {...register("password")}
                disabled={isLoading}
                className={`h-16 rounded-xl border-2 text-xl font-normal md:text-3xl placeholder:text-slate-300 px-6 ${
                  errors.password ? 'border-red-500' : 'border-slate-200'
                }`}
              />
              <ErrorMessage message={errors.password?.message} />
            </div>

            {/* 비밀번호 확인 필드 */}
            <div className="space-y-3">
              <Label
                htmlFor="confirmPassword"
                className="text-2xl font-semibold text-slate-800 md:text-3xl"
              >
                비밀번호 확인
              </Label>
              <Input
                type="password"
                id="confirmPassword"
                placeholder="비밀번호를 입력하세요"
                {...register("confirmPassword")}
                disabled={isLoading}
                className={`h-16 rounded-xl border-2 text-xl font-normal md:text-3xl placeholder:text-slate-300 px-6 ${
                  errors.confirmPassword ? 'border-red-500' : 'border-slate-200'
                }`}
              />
              <ErrorMessage message={errors.confirmPassword?.message} />
            </div>

            {/* 회원가입 버튼 */}
            <Button
              type="submit"
              disabled={isLoading}
              size="lg"
              className="w-full bg-green-500 hover:bg-green-600 text-white"
            >
              {isLoading ? "가입 중..." : "회원가입"}
            </Button>
          </form>
        </CardContent>
        <CardFooter className="flex-col sm:flex-row justify-center items-baseline pt-8">
          <p className="text-lg font-semibold text-slate-500 md:text-2xl">
            이미 계정이 있으신가요?&nbsp;
          </p>
          <Button
            variant="link"
            onClick={handleToggleMode}
            disabled={isLoading}
            className="p-0 text-lg font-semibold text-blue-600 md:text-2xl"
          >
            로그인
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
};

export default SignupPage;
