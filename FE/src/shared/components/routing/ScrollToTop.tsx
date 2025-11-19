import { useEffect } from 'react';
import { useLocation, useNavigationType } from 'react-router-dom';

/**
 * 라우트 변경 시 페이지 최상단으로 스크롤하는 컴포넌트
 * 
 * - 경로(pathname), 쿼리 파라미터(search), 해시(hash) 변경 시 동작
 * - 뒤로가기/앞으로가기(POP)일 때는 브라우저 자동 스크롤 복원 사용
 * - 해시가 있는 경우는 브라우저 기본 동작(해시 위치로 스크롤) 유지
 * - 해시가 있지만 대상 엘리먼트가 없으면 최상단으로 스크롤
 * - scrollRestoration을 적절히 관리하여 전역 설정이 남지 않도록 처리
 */
export default function ScrollToTop() {
  const { pathname, hash, search } = useLocation();
  const navType = useNavigationType(); // 'PUSH' | 'POP' | 'REPLACE'

  useEffect(() => {
    // 뒤/앞으로 가기(POP): 브라우저의 스크롤 복원 사용
    if (navType === 'POP') {
      if ('scrollRestoration' in window.history) {
        window.history.scrollRestoration = 'auto';
      }
      return;
    }

    // 해시가 있고 대상 엘리먼트가 존재하면 브라우저 기본 동작 유지
    if (hash) {
      const id = hash.slice(1);
      const el = document.getElementById(id);
      if (el) {
        // 해시 점프에서도 복원 동작이 필요하므로 안전하게 auto 유지
        if ('scrollRestoration' in window.history) {
          window.history.scrollRestoration = 'auto';
        }
        return;
      }
      // 해시 대상이 없으면 최상단으로 스크롤
    }

    // 새 이동(PUSH/REPLACE): 수동 제어 후 곧바로 원복
    if ('scrollRestoration' in window.history) {
      window.history.scrollRestoration = 'manual';
    }

    window.scrollTo({ top: 0, left: 0, behavior: 'smooth' });

    // 다음 틱에 auto로 원복(전역 설정이 남지 않게)
    if (typeof queueMicrotask !== 'undefined') {
      queueMicrotask(() => {
        if ('scrollRestoration' in window.history) {
          window.history.scrollRestoration = 'auto';
        }
      });
    } else {
      // queueMicrotask가 없는 환경을 위한 fallback
      setTimeout(() => {
        if ('scrollRestoration' in window.history) {
          window.history.scrollRestoration = 'auto';
        }
      }, 0);
    }
  }, [pathname, search, hash, navType]);

  // 컴포넌트가 언마운트될 때도 안전하게 auto로
  useEffect(() => {
    return () => {
      if ('scrollRestoration' in window.history) {
        window.history.scrollRestoration = 'auto';
      }
    };
  }, []);

  return null;
}

