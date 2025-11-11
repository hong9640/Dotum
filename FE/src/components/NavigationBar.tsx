import React from 'react';
import { LogOut, LogIn } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useTrainingSession } from '@/hooks/training-session';
import { useAlertDialog } from '@/hooks/useAlertDialog';

interface NavigationBarProps {
  isLoggedIn: boolean;
  onLogout: () => void;
}

const NavigationBar: React.FC<NavigationBarProps> = ({ isLoggedIn, onLogout }) => {
  const navigate = useNavigate();
  const { createWordSession, createSentenceSession, isLoading } = useTrainingSession();
  const { showAlert, AlertDialog: LoginRequiredDialog } = useAlertDialog();

  // 로그인이 필요한 경우 알림
  const handleAuthRequired = () => {
    showAlert({
      title: '로그인이 필요합니다',
      description: '로그인 페이지로 이동합니다.',
      onConfirm: () => navigate('/login')
    });
  };

  const handleWordTraining = async (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault();
    
    // 인증 상태 확인 (prop으로 전달받은 실제 인증 상태 사용)
    if (!isLoggedIn) {
      handleAuthRequired();
      return;
    }
    
    // 로그인한 상태면 바로 시작
    try {
      await createWordSession(10); // 10개 단어
    } catch (error) {
      // 에러는 훅에서 처리됨
      console.error('단어 훈련 세션 생성 실패:', error);
    }
  };

  const handleSentenceTraining = async (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault();
    
    // 인증 상태 확인 (prop으로 전달받은 실제 인증 상태 사용)
    if (!isLoggedIn) {
      handleAuthRequired();
      return;
    }
    
    // 로그인한 상태면 바로 시작
    try {
      await createSentenceSession(10); // 10개 문장
    } catch (error) {
      // 에러는 훅에서 처리됨
      console.error('문장 훈련 세션 생성 실패:', error);
    }
  };

  const handleMaxVoiceTraining = (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault();
    
    // 인증 상태 확인
    if (!isLoggedIn) {
      handleAuthRequired();
      return;
    }
    
    // 발성 훈련 페이지로 이동
    navigate('/voice-training');
  };

  return (
    <>
      {/* 로그인 필요 다이얼로그 */}
      <LoginRequiredDialog />
      
      <nav className="w-full bg-white shadow-[0px_1px_2px_0px_rgba(0,0,0,0.05)] border-b border-gray-200">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 sm:h-24 items-center justify-between">
          {/* 로고 섹션 */}
          <div className="flex-shrink-0">
            <a href="/" className="flex items-center">
              {/* <span className="mr-1 text-3xl font-semibold text-slate-700 leading-10">
                🌿
              </span> */}
              <span className="mr-1.5 text-2xl lg:text-3xl font-semibold text-slate-700 leading-10">
                🌱
              </span>
              <span className="text-3xl lg:text-4xl font-semibold text-slate-700 leading-10">
                돋음
              </span>
            </a>
          </div>

          {/* 네비게이션 메뉴 섹션 */}
          <div className="flex items-center space-x-3 md:space-x-6">
            <a
              href="/voice-training"
              onClick={handleMaxVoiceTraining}
              className={`hidden sm:block px-3 py-2 text-2xl font-semibold text-slate-700 rounded-md hover:bg-gray-100 transition-colors duration-200 lg:text-3xl ${isLoading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
            >
              발성 연습
            </a>
            <a
              href="/practice"
              onClick={handleWordTraining}
              className={`hidden sm:block px-3 py-2 text-2xl font-semibold text-slate-700 rounded-md hover:bg-gray-100 transition-colors duration-200 lg:text-3xl ${isLoading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
            >
              단어 연습
            </a>
            <a
              href="/practice"
              onClick={handleSentenceTraining}
              className={`hidden sm:block px-3 py-2 text-2xl font-semibold text-slate-700 rounded-md hover:bg-gray-100 transition-colors duration-200 lg:text-3xl ${isLoading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
            >
              문장 연습
            </a>
            <Link
              to="/training-history"
              className="hidden sm:block px-3 py-2 text-2xl font-semibold text-slate-700 rounded-md hover:bg-gray-100 transition-colors duration-200 lg:text-3xl"
            >
              훈련 기록
            </Link>
            {/* 로그인 상태에 따른 버튼 렌더링 */}
            {isLoggedIn ? (
              <button
                type="button"
                onClick={onLogout}
                className="flex items-center gap-2 px-3 py-2 text-2xl font-semibold text-slate-700 rounded-md hover:bg-gray-100 transition-colors duration-200 lg:text-3xl"
              >
                <LogOut className="h-7 w-7 lg:h-8 lg:w-8" strokeWidth={2.5} />
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
    </>
  );
};

export default NavigationBar;
