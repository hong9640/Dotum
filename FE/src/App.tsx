import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom';
import NavigationBar from '@/components/NavigationBar';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import HomePage from '@/pages/home';
import PracticePage from '@/pages/practice';
import LoginPage from '@/pages/login';
import SignupPage from '@/pages/signup';
import WordSetResults from '@/pages/result-list';
import ResultDetailPage from '@/pages/result-detail';
import TrainingHistoryPage from '@/pages/training-history';
import VoiceTrainingIntro from '@/pages/voice-training';
import MPTPage from '@/pages/voice-training/mpt';
import CrescendoPage from '@/pages/voice-training/crescendo';
import DecrescendoPage from '@/pages/voice-training/decrescendo';
import LoudSoftPage from '@/pages/voice-training/loud-soft';
import SoftLoudPage from '@/pages/voice-training/soft-loud';
import { clearAuthCookies } from '@/lib/cookies';
import { checkAuthStatus } from '@/api/user';
import { Logout } from '@/api/logout/Logout';
import { toast } from 'sonner';

const AppContent: React.FC<{
  isLoggedIn: boolean;
  handleLogin: () => void;
  handleLogout: () => void;
  handleSignup: () => void;
}> = ({ isLoggedIn, handleLogin, handleLogout, handleSignup }) => {
  const navigate = useNavigate();

  const onLogoutClick = async () => {
    try {
      const result = await Logout();
      
      if (result.status === "SUCCESS") {
        toast.success("로그아웃되었습니다.");
        handleLogout();
        navigate('/');
      } else {
        toast.error(result.error?.message || "로그아웃에 실패했습니다.");
      }
    } catch (error) {
      // API 실패해도 클라이언트 로그아웃 처리
      clearAuthCookies();
      handleLogout();
      navigate('/');
    }
  };

  return (
    <div className="flex flex-col min-h-screen bg-white">
      <NavigationBar isLoggedIn={isLoggedIn} onLogout={onLogoutClick} />
      <main className="flex-1">
        <Routes>
          {/* 공개 페이지 */}
          <Route path="/" element={<HomePage />} />
          
          {/* 로그인 필요 페이지 */}
          <Route 
            path="/practice" 
            element={
              <ProtectedRoute isLoggedIn={isLoggedIn} requireAuth={true}>
                <PracticePage />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/result-list" 
            element={
              <ProtectedRoute isLoggedIn={isLoggedIn} requireAuth={true}>
                <WordSetResults />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/result-detail" 
            element={
              <ProtectedRoute isLoggedIn={isLoggedIn} requireAuth={true}>
                <ResultDetailPage />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/training-history" 
            element={
              <ProtectedRoute isLoggedIn={isLoggedIn} requireAuth={true}>
                <TrainingHistoryPage />
              </ProtectedRoute>
            } 
          />
          
          {/* 발성 연습 페이지 */}
          <Route 
            path="/voice-training" 
            element={
              <ProtectedRoute isLoggedIn={isLoggedIn} requireAuth={true}>
                <VoiceTrainingIntro />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/voice-training/mpt" 
            element={
              <ProtectedRoute isLoggedIn={isLoggedIn} requireAuth={true}>
                <MPTPage />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/voice-training/crescendo" 
            element={
              <ProtectedRoute isLoggedIn={isLoggedIn} requireAuth={true}>
                <CrescendoPage />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/voice-training/decrescendo" 
            element={
              <ProtectedRoute isLoggedIn={isLoggedIn} requireAuth={true}>
                <DecrescendoPage />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/voice-training/loud-soft" 
            element={
              <ProtectedRoute isLoggedIn={isLoggedIn} requireAuth={true}>
                <LoudSoftPage />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/voice-training/soft-loud" 
            element={
              <ProtectedRoute isLoggedIn={isLoggedIn} requireAuth={true}>
                <SoftLoudPage />
              </ProtectedRoute>
            } 
          />
          
          {/* 비로그인 전용 페이지 */}
          <Route 
            path="/login" 
            element={
              <ProtectedRoute isLoggedIn={isLoggedIn} requireAuth={false}>
                <LoginPage onLogin={handleLogin} />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/signup" 
            element={
              <ProtectedRoute isLoggedIn={isLoggedIn} requireAuth={false}>
                <SignupPage onSignup={handleSignup} />
              </ProtectedRoute>
            } 
          />
        </Routes>
      </main>
    </div>
  );
};

const App: React.FC = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [isAuthChecking, setIsAuthChecking] = useState(true);

  const handleLogin = () => {
    setIsLoggedIn(true);
  };

  const handleLogout = () => {
    clearAuthCookies();
    setIsLoggedIn(false);
  };

  const handleSignup = () => {
    setIsLoggedIn(true);
  };

  // 초기 로드 시 인증 상태 확인 (리다이렉트 없이)
  useEffect(() => {
    const verifyAuth = async () => {
      const authenticated = await checkAuthStatus();
      setIsLoggedIn(authenticated);
      setIsAuthChecking(false);
    };
    
    verifyAuth();
  }, []);

  // 인증 확인 중에는 빈 화면 또는 로딩 표시
  if (isAuthChecking) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-white">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent align-[-0.125em] motion-reduce:animate-[spin_1.5s_linear_infinite]" role="status">
            <span className="!absolute !-m-px !h-px !w-px !overflow-hidden !whitespace-nowrap !border-0 !p-0 ![clip:rect(0,0,0,0)]">로딩중...</span>
          </div>
          <p className="mt-4 text-slate-600">로딩 중...</p>
        </div>
      </div>
    );
  }

  return (
    <Router>
      <AppContent 
        isLoggedIn={isLoggedIn}
        handleLogin={handleLogin}
        handleLogout={handleLogout}
        handleSignup={handleSignup}
      />
    </Router>
  );
};

export default App
