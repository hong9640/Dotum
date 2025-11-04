import React from 'react';
import { LogOut, LogIn } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { useTrainingSession } from '@/hooks/training-session';

interface NavigationBarProps {
  isLoggedIn: boolean;
  onLogout: () => void;
}

const NavigationBar: React.FC<NavigationBarProps> = ({ isLoggedIn, onLogout }) => {
  const navigate = useNavigate();
  const { createWordSession, createSentenceSession, isLoading } = useTrainingSession();

  // 인증 상태 확인 (localStorage auth 플래그 기준)
  const checkAuthStatus = () => {
    const isAuthenticated = localStorage.getItem('auth') === 'true';
    console.log('🔍 인증 상태 확인(auth 플래그):', isAuthenticated ? '인증됨' : '인증 안됨');
    return isAuthenticated;
  };

  // 로그인이 필요한 경우 알림
  const handleAuthRequired = () => {
    toast.error("로그인이 필요합니다. 먼저 로그인해주세요.");
    // 로그인 페이지로 이동
    navigate('/login');
  };

  const handleWordTraining = async (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault();
    console.log('🚀 단어 훈련 시작 버튼 클릭');
    
    // 인증 상태 확인
    if (!checkAuthStatus()) {
      console.error('❌ 토큰이 없습니다. 로그인이 필요합니다.');
      handleAuthRequired();
      return;
    }
    
    try {
      await createWordSession(2); // 2개 단어 -> 이후에 훈련 당 아이템 개수는 조정할 예정
    } catch (error) {
      // 에러는 훅에서 처리됨
      console.error('단어 훈련 세션 생성 실패:', error);
    }
  };

  const handleSentenceTraining = async (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault();
    console.log('🚀 문장 훈련 시작 버튼 클릭');
    
    // 인증 상태 확인
    if (!checkAuthStatus()) {
      console.error('❌ 토큰이 없습니다. 로그인이 필요합니다.');
      handleAuthRequired();
      return;
    }
    
    try {
      await createSentenceSession(2); // 2개 문장
    } catch (error) {
      // 에러는 훅에서 처리됨
      console.error('문장 훈련 세션 생성 실패:', error);
    }
  };

  return (
    <nav className="w-full bg-white shadow-[0px_1px_2px_0px_rgba(0,0,0,0.05)] border-b border-gray-200">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-24 items-center justify-between">
          {/* 로고 섹션 */}
          <div className="flex-shrink-0">
            <a href="/" className="flex items-center">
              <span className="mr-1.5 text-3xl font-semibold text-slate-700 leading-10">
                🌱
              </span>
              <span className="text-4xl font-semibold text-slate-700 leading-10">
                돋음
              </span>
            </a>
          </div>

          {/* 네비게이션 메뉴 섹션 */}
          <div className="flex items-center space-x-3 md:space-x-6">
            <a
              href="/practice"
              onClick={handleWordTraining}
              className={`px-3 py-2 text-2xl font-semibold text-slate-700 rounded-md hover:bg-gray-100 transition-colors duration-200 [@media(min-width:850px)]:text-3xl ${isLoading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
            >
              단어 연습
            </a>
            <a
              href="/practice"
              onClick={handleSentenceTraining}
              className={`px-3 py-2 text-2xl font-semibold text-slate-700 rounded-md hover:bg-gray-100 transition-colors duration-200 [@media(min-width:850px)]:text-3xl ${isLoading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
            >
              문장 연습
            </a>
            <Link
              to="/training-history"
              className="px-3 py-2 text-2xl font-semibold text-slate-700 rounded-md hover:bg-gray-100 transition-colors duration-200 [@media(min-width:850px)]:text-3xl"
            >
              훈련기록
            </Link>
            {/* 로그인 상태에 따른 버튼 렌더링 */}
            {isLoggedIn ? (
              <button
                type="button"
                onClick={onLogout}
                className="flex items-center gap-2 px-3 py-2 text-2xl font-semibold text-slate-700 rounded-md hover:bg-gray-100 transition-colors duration-200 [@media(min-width:850px)]:text-3xl"
              >
                <LogOut className="h-7 w-7 [@media(min-width:850px)]:h-8 [@media(min-width:850px)]:w-8" strokeWidth={2.5} />
                <span className="hidden md:flex">로그아웃</span>
              </button>
            ) : (
              <Link
                to="/login"
                className="flex items-center gap-2 px-3 py-2 text-xl font-semibold text-slate-700 rounded-md hover:bg-gray-100 transition-colors duration-200 [@media(min-width:850px)]:text-3xl"
              >
                <LogIn className="h-7 w-7 [@media(min-width:850px)]:h-8 [@media(min-width:850px)]:w-8" strokeWidth={2.5} />
                <span className="hidden md:flex">로그인</span>
              </Link>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default NavigationBar;
