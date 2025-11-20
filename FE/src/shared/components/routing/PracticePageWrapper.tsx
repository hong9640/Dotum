import React from 'react';
import { useSearchParams } from 'react-router-dom';
import PracticePage from '@/features/practice/pages/PracticePage';

/**
 * PracticePage를 sessionId와 type으로 완전히 새로 생성하는 Wrapper
 * URL 파라미터가 변경될 때마다 PracticePage를 완전히 새로 마운트하여 상태 초기화
 */
const PracticePageWrapper: React.FC = () => {
  const [searchParams] = useSearchParams();
  const sessionId = searchParams.get('sessionId');
  const type = searchParams.get('type');
  
  // sessionId와 type이 바뀔 때마다 PracticePage를 완전히 새로 생성
  return <PracticePage key={`${sessionId}-${type}`} />;
};

export default PracticePageWrapper;

