import React from 'react';
import { LogOut, LogIn } from 'lucide-react';
import { Link } from 'react-router-dom';

interface NavigationBarProps {
  isLoggedIn: boolean;
  onLogout: () => void;
}

const NavigationBar: React.FC<NavigationBarProps> = ({ isLoggedIn, onLogout }) => {

  return (
    <nav className="w-full bg-white shadow-[0px_1px_2px_0px_rgba(0,0,0,0.05)] border-b border-gray-200">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-24 items-center justify-between">
          {/* 로고 섹션 */}
          <div className="flex-shrink-0">
            <a href="/" className="flex items-center">
              <span className="text-4xl font-normal text-green-700 font-['ADLaM_Display'] leading-10">
                Dodeum
              </span>
            </a>
          </div>

          {/* 네비게이션 메뉴 섹션 */}
          <div className="flex items-center space-x-4 md:space-x-6">
            <Link
              to="/practice"
              className="px-3 py-2 text-xl font-semibold text-slate-700 rounded-md hover:bg-gray-100 transition-colors duration-200 md:text-3xl"
            >
              발음 훈련
            </Link>
            <Link
              to="/training-history"
              className="px-3 py-2 text-xl font-semibold text-slate-700 rounded-md hover:bg-gray-100 transition-colors duration-200 md:text-3xl"
            >
              훈련기록
            </Link>
            {/* 로그인 상태에 따른 버튼 렌더링 */}
            {isLoggedIn ? (
              <button
                type="button"
                onClick={onLogout}
                className="flex items-center gap-2 px-3 py-2 text-xl font-semibold text-slate-700 rounded-md hover:bg-gray-100 transition-colors duration-200 md:text-3xl"
              >
                <LogOut className="h-7 w-7 md:h-8 md:w-8" strokeWidth={2.5} />
                <span>로그아웃</span>
              </button>
            ) : (
              <Link
                to="/login"
                className="flex items-center gap-2 px-3 py-2 text-xl font-semibold text-slate-700 rounded-md hover:bg-gray-100 transition-colors duration-200 md:text-3xl"
              >
                <LogIn className="h-7 w-7 md:h-8 md:w-8" strokeWidth={2.5} />
                <span>로그인</span>
              </Link>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default NavigationBar;
