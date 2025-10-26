import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { toast } from 'sonner';

// 에러 매핑 테이블
const ERROR_MAPPING = {
  USERNAME_ALREADY_EXISTS: "이미 등록된 이메일입니다.",
  INVALID_PHONE_NUMBER: "올바른 전화번호를 입력해주세요.",
  INVALID_GENDER: "성별을 선택해주세요.",
} as const;

// Zod 유효성 검사 스키마
const signupSchema = z
  .object({
    username: z.string().email("유효한 이메일 형식이 아닙니다."),
    password: z.string().min(8, "비밀번호는 8자 이상이어야 합니다."),
    confirmPassword: z.string(),
    name: z.string().min(1, "이름을 입력해주세요."),
    phone_number: z.string().min(1, "전화번호를 입력해주세요."),
    gender: z.enum(["MALE", "FEMALE"], { message: "성별을 선택해주세요." })
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "비밀번호가 일치하지 않습니다.",
    path: ["confirmPassword"],
  });

type SignupFormValues = z.infer<typeof signupSchema>;

interface SignupPageProps {
  onSignup: () => void;
}

const SignupPage: React.FC<SignupPageProps> = ({ onSignup }) => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  const form = useForm<SignupFormValues>({
    resolver: zodResolver(signupSchema),
    defaultValues: {
      username: '',
      password: '',
      confirmPassword: '',
      name: '',
      phone_number: '',
      gender: undefined,
    },
  });

  const { register, handleSubmit, formState: { errors }, watch, setValue } = form;

  // 전화번호 포맷팅 함수
  const formatPhoneDisplay = (value: string) => {
    const numbers = value.replace(/\D/g, '');
    if (numbers.length <= 3) return numbers;
    if (numbers.length <= 7) return `${numbers.slice(0, 3)}-${numbers.slice(3)}`;
    return `${numbers.slice(0, 3)}-${numbers.slice(3, 7)}-${numbers.slice(7, 11)}`;
  };

  const phoneValue = watch("phone_number") || "";

  const onSubmit = async (data: SignupFormValues) => {
    setIsLoading(true);
    setApiError(null);
    
    try {
      const response = await fetch('/api/v1/auth/signup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: data.username,
          password: data.password,
          name: data.name,
          phone_number: data.phone_number,
          gender: data.gender
        })
      });
      
      const result = await response.json();
      
      if (response.ok && result.status === "SUCCESS") {
        toast.success("회원가입이 완료되었습니다!");
        onSignup();
        navigate('/login');
      } else {
        const errorMessage = ERROR_MAPPING[result.error?.code as keyof typeof ERROR_MAPPING] || result.error?.message || "회원가입에 실패했습니다.";
        setApiError(errorMessage);
      }
    } catch {
      setApiError("네트워크 오류가 발생했습니다. 다시 시도해주세요.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleMode = () => {
    navigate('/login');
  };

  // 에러 메시지 컴포넌트
  const ErrorMessage = ({ message, id }: { message?: string; id?: string }) => (
    <>
    {message && (
    <div className="h-7 flex items-start">
      {message && (
        <div id={id} className="text-red-500 text-xl font-semibold">
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
          {/* API 에러 메시지 */}
          {apiError && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <div className="text-red-700 font-medium text-xl">{apiError}</div>
            </div>
          )}
          
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
            {/* 이메일 필드 */}
            <div className="space-y-3">
              <Label
                htmlFor="username"
                className="text-2xl font-semibold text-slate-800 md:text-3xl"
              >
                이메일
              </Label>
              <Input
                type="email"
                id="username"
                placeholder="이메일을 입력하세요"
                {...register("username")}
                disabled={isLoading}
                aria-invalid={!!errors.username}
                aria-describedby={errors.username ? "username-error" : undefined}
                className={`h-16 rounded-xl border-2 text-xl font-normal md:text-3xl placeholder:text-slate-300 px-6 ${
                  errors.username ? 'border-red-500' : 'border-slate-200'
                }`}
              />
              <ErrorMessage message={errors.username?.message} id="username-error" />
            </div>

            {/* 이름 필드 */}
            <div className="space-y-3">
              <Label
                htmlFor="name"
                className="text-2xl font-semibold text-slate-800 md:text-3xl"
              >
                이름
              </Label>
              <Input
                type="text"
                id="name"
                placeholder="이름을 입력하세요"
                {...register("name")}
                disabled={isLoading}
                aria-invalid={!!errors.name}
                aria-describedby={errors.name ? "name-error" : undefined}
                className={`h-16 rounded-xl border-2 text-xl font-normal md:text-3xl placeholder:text-slate-300 px-6 ${
                  errors.name ? 'border-red-500' : 'border-slate-200'
                }`}
              />
              <ErrorMessage message={errors.name?.message} id="name-error" />
            </div>

            {/* 전화번호 필드 */}
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
                  const numbers = e.target.value.replace(/\D/g, '');
                  setValue("phone_number", numbers);
                }}
                disabled={isLoading}
                aria-invalid={!!errors.phone_number}
                aria-describedby={errors.phone_number ? "phone-error" : undefined}
                className={`h-16 rounded-xl border-2 text-xl font-normal md:text-3xl placeholder:text-slate-300 px-6 ${
                  errors.phone_number ? 'border-red-500' : 'border-slate-200'
                }`}
              />
              <ErrorMessage message={errors.phone_number?.message} id="phone-error" />
            </div>

            {/* 성별 필드 */}
            <div className="space-y-3">
              <Label className="text-2xl font-semibold text-slate-800 md:text-3xl">
                성별
              </Label>
              <RadioGroup
                {...register("gender")}
                disabled={isLoading}
                aria-invalid={!!errors.gender}
                aria-describedby={errors.gender ? "gender-error" : undefined}
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
              <ErrorMessage message={errors.gender?.message} id="gender-error" />
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
                aria-invalid={!!errors.password}
                aria-describedby={errors.password ? "password-error" : undefined}
                className={`h-16 rounded-xl border-2 text-xl font-normal md:text-3xl placeholder:text-slate-300 px-6 ${
                  errors.password ? 'border-red-500' : 'border-slate-200'
                }`}
              />
              <ErrorMessage message={errors.password?.message} id="password-error" />
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
                aria-invalid={!!errors.confirmPassword}
                aria-describedby={errors.confirmPassword ? "confirm-password-error" : undefined}
                className={`h-16 rounded-xl border-2 text-xl font-normal md:text-3xl placeholder:text-slate-300 px-6 ${
                  errors.confirmPassword ? 'border-red-500' : 'border-slate-200'
                }`}
              />
              <ErrorMessage message={errors.confirmPassword?.message} id="confirm-password-error" />
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
