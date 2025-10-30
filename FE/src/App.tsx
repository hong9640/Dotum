import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import NavigationBar from '@/components/NavigationBar';
import HomePage from '@/pages/home';
import PracticePage from '@/pages/practice';
import LoginPage from '@/pages/login';
import SignupPage from '@/pages/signup';
import WordSetResults from '@/pages/result-list';
import TrainingHistoryPage from '@/pages/training-history';
import { clearAuthCookies } from '@/lib/cookies';

const App: React.FC = () => {
  // 전역 로그인 상태 관리
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  const handleLogin = () => {
    // auth 플래그 true 설정
    localStorage.setItem('auth', 'true');
    setIsLoggedIn(true);
  };

  const handleLogout = () => {
    console.log('🚪 로그아웃 처리 중...');
    // 인증 쿠키 삭제
    clearAuthCookies();
    // 로그인 상태 변경
    localStorage.setItem('auth', 'false');
    setIsLoggedIn(false);
    console.log('✅ 로그아웃 완료');
  };

  const handleSignup = () => {
    setIsLoggedIn(true);
  };

  // 초기 로드 시 auth 플래그 기본값 설정 및 상태 동기화
  useEffect(() => {
    const existing = localStorage.getItem('auth');
    if (existing === null) {
      localStorage.setItem('auth', 'false');
    }
    setIsLoggedIn(localStorage.getItem('auth') === 'true');
  }, []);

  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
      {/* <div className="min-h-screen bg-white"> */}
        <NavigationBar isLoggedIn={isLoggedIn} onLogout={handleLogout} />
        <main>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/practice" element={<PracticePage />} />
            <Route path="/login" element={<LoginPage onLogin={handleLogin} />} />
            <Route path="/signup" element={<SignupPage onSignup={handleSignup} />} />
            <Route path="/result-list" element={<WordSetResults />} />
            <Route path="/training-history" element={<TrainingHistoryPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
};

export default App
