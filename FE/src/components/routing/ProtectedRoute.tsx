import { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';

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
  const [showLoginDialog, setShowLoginDialog] = useState(false);
  const [shouldRedirect, setShouldRedirect] = useState(false);

  // 로그인 필요한데 로그인 안됨
  useEffect(() => {
    if (requireAuth && !isLoggedIn) {
      setShowLoginDialog(true);
    }
  }, [requireAuth, isLoggedIn]);

  const handleLoginConfirm = () => {
    setShowLoginDialog(false);
    setShouldRedirect(true);
  };

  // 다이얼로그 확인 후 리다이렉트
  if (requireAuth && !isLoggedIn && shouldRedirect) {
    return <Navigate to={redirectTo || '/login'} replace />;
  }

  // 비로그인 필요한데 로그인됨
  if (requireAuth === false && isLoggedIn) {
    return <Navigate to={redirectTo || '/'} replace />;
  }

  // 로그인 필요한데 로그인 안 됨 - 다이얼로그 표시
  if (requireAuth && !isLoggedIn) {
    return (
      <>
        <AlertDialog open={showLoginDialog} onOpenChange={setShowLoginDialog}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle className="text-2xl">로그인이 필요합니다</AlertDialogTitle>
              <AlertDialogDescription className="text-lg">
                로그인 페이지로 이동합니다.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogAction 
                onClick={handleLoginConfirm}
                className="text-lg px-6 py-4"
              >
                확인
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
        {/* 빈 화면 표시 */}
        <div className="flex items-center justify-center min-h-screen bg-white" />
      </>
    );
  }

  return children;
};

