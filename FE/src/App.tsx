import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import NavigationBar from '@/components/NavigationBar';
import HomePage from '@/pages/home';
import PracticePage from '@/pages/practice';
import LoginPage from '@/pages/login';
import SignupPage from '@/pages/signup';
import WordSetResults from '@/pages/result-list';
import TrainingHistoryPage from '@/pages/training-history';

const App: React.FC = () => {
  // 전역 로그인 상태 관리
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  const handleLogin = () => {
    setIsLoggedIn(true);
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
  };

  const handleSignup = () => {
    setIsLoggedIn(true);
  };

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
