import type { TrainingSet } from './types';

// 동적으로 샘플 데이터 생성하는 함수
export const generateSampleData = (count: number, date: string): TrainingSet[] => {
  const wordSets = [
    ['사과', '바나나', '딸기'],
    ['포도', '오렌지', '수박'],
    ['체리', '복숭아', '자두'],
    ['키위', '파인애플', '망고'],
    ['레몬', '라임', '자몽'],
    ['아보카도', '코코넛', '석류']
  ];
  
  const scores = [74, 85, 45, 45, 20, 20]; // 다양한 점수 샘플
  const letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'];
  
  return Array.from({ length: count }, (_, index) => ({
    id: `${index + 1}`,
    title: `단어 세트 ${letters[index] || String.fromCharCode(65 + index)}`,
    score: scores[index % scores.length],
    words: wordSets[index % wordSets.length],
    completedAt: new Date(date).toISOString()
  }));
};
