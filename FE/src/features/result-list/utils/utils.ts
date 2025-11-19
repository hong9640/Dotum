import type { WordResult } from '@/features/result-list/types';

/**
 * WordResult 더미데이터 생성 함수 (나중에 백엔드 API로 교체 예정)
 * result-list 페이지에서 사용
 * 
 * @param count 생성할 데이터 개수
 * @returns WordResult 배열
 */
export const generateDummyWordResults = (count: number): WordResult[] => {
  const dummyWords = [
    '사과', '바나나', '딸기', '포도', '오렌지',
    '수박', '체리', '복숭아', '자두', '키위'
  ];
  const dummyFeedbacks = [
    '아주 잘했어요!',
    '좋은 발음이에요.',
    '조금 더 연습이 필요해요.',
    '훌륭합니다!',
    '잘 하고 있어요.',
    '계속 연습해봐요.',
    '좋아요!',
    '좀 더 노력해봐요.',
    '괜찮아요.',
    '잘했어요!'
  ];
  const dummyScores = [95, 87, 75, 92, 88, 82, 90, 76, 85, 93];

  return Array.from({ length: count }, (_, index) => ({
    id: index + 1,
    word: dummyWords[index % dummyWords.length],
    feedback: dummyFeedbacks[index % dummyFeedbacks.length],
    score: dummyScores[index % dummyScores.length]
  }));
};


