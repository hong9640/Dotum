import { useEffect } from 'react';
import { Navigate } from 'react-router-dom';

interface ProtectedRouteProps {
  children: React.ReactElement;
  isLoggedIn: boolean;
  requireAuth?: boolean; // true: 로그인 필요, false: 비로그인만 가능
  redirectTo?: string;
}

/**
 * 라우터 가드 컴포넌트 (isLoggedIn 상태 기반)
 */
export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  isLoggedIn,
  requireAuth,
  redirectTo,
}) => {
  // 로그인 필요한데 로그인 안됨
  if (requireAuth && !isLoggedIn) {
    useEffect(() => {
      alert('로그인이 필요합니다.\n로그인 페이지로 이동합니다.');
    }, []);
    return <Navigate to={redirectTo || '/login'} replace />;
  }

  // 비로그인 필요한데 로그인됨
  if (requireAuth === false && isLoggedIn) {
    return <Navigate to={redirectTo || '/'} replace />;
  }

  return children;
};

