import React from 'react';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';

interface LoginPageProps {
  onLogin: () => void;
}

const LoginPage: React.FC<LoginPageProps> = ({ onLogin }) => {
  const navigate = useNavigate();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // 로그인 로직 처리
    console.log('로그인 시도');
    
    // 로그인 성공 시
    onLogin();
    navigate('/'); // 홈페이지로 리다이렉트
  };

  return (
    // 페이지 전체를 채우고 중앙 정렬합니다.
    <div className="w-full flex justify-center items-center py-12 px-4">
      {/* 사용자가 요청한 w-[672px]와 유사하게 max-w-2xl (672px)을 설정합니다. */}
      <Card className="w-full max-w-2xl">
        <CardHeader>
          {/* 사용자가 요청한 text-5xl 폰트를 반응형으로 적용합니다. */}
          <CardTitle className="text-center text-4xl font-extrabold font-['Pretendard'] md:text-5xl text-slate-800 py-6">
            로그인
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-8">
            {/* 이메일 필드 */}
            <div className="space-y-3">
              {/* 사용자가 요청한 text-3xl 폰트를 반응형으로 적용합니다. */}
              <Label
                htmlFor="email"
                className="text-2xl font-semibold font-['Pretendard'] text-slate-800 md:text-3xl"
              >
                이메일
              </Label>
              {/* 사용자가 요청한 h-16, text-3xl 폰트를 반응형으로 적용합니다. */}
              <Input
                type="email"
                id="email"
                placeholder="이메일을 입력하세요"
                className="h-16 rounded-xl border-2 border-slate-200 text-xl font-semibold font-['Pretendard'] md:text-3xl placeholder:text-slate-300"
              />
            </div>
            {/* 비밀번호 필드 */}
            <div className="space-y-3">
              <Label
                htmlFor="password"
                className="text-2xl font-semibold font-['Pretendard'] text-slate-800 md:text-3xl"
              >
                비밀번호
              </Label>
              <Input
                type="password"
                id="password"
                placeholder="비밀번호를 입력하세요"
                className="h-16 rounded-xl border-2 border-slate-200 text-xl font-semibold font-['Pretendard'] md:text-3xl placeholder:text-slate-300"
              />
            </div>
            {/* 로그인 버튼 */}
            <Button
              type="submit"
              // 사용자가 요청한 스타일(녹색 배경, 큰 폰트)을 적용합니다.
              className="w-full h-auto py-4 bg-green-500 text-white hover:bg-green-600 rounded-xl text-2xl font-semibold font-['Pretendard'] md:text-3xl"
            >
              로그인
            </Button>
          </form>
        </CardContent>
        <CardFooter className="flex-col sm:flex-row justify-center items-baseline pt-8">
          {/* 사용자가 요청한 text-3xl 폰트를 반응형으로 적용합니다. */}
          <p className="text-lg font-semibold font-['Pretendard'] text-slate-500 md:text-2xl">
            회원이 아니신가요?&nbsp;
          </p>
          <Button
            variant="link"
            className="p-0 text-lg font-semibold font-['Pretendard'] text-blue-600 md:text-2xl"
          >
            회원가입
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
};

export default LoginPage;
