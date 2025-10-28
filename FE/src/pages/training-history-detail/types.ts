// 훈련 세트 데이터 타입
export interface TrainingSet {
  id: string;
  title: string;
  score: number;
  words: string[];
  completedAt: string; // ISO date string
}

// 점수별 색상 규칙을 위한 타입
export type ScoreLevel = 'high' | 'medium' | 'low';

// 점수에 따른 색상 레벨 반환 함수
export const getScoreLevel = (score: number): ScoreLevel => {
  if (score >= 70) return 'high';
  if (score >= 40) return 'medium';
  return 'low';
};

// 점수별 색상 클래스 매핑
export const scoreColorClasses = {
  high: {
    background: 'bg-blue-100',
    backgroundHover: 'hover:bg-blue-50',
    border: 'border-blue-300',
    text: 'text-blue-600',
    outline: 'outline-blue-300'
  },
  medium: {
    background: 'bg-green-100',
    backgroundHover: 'hover:bg-green-50',
    border: 'border-green-300',
    text: 'text-green-600',
    outline: 'outline-green-300'
  },
  low: {
    background: 'bg-amber-100',
    backgroundHover: 'hover:bg-amber-50',
    border: 'border-amber-300',
    text: 'text-amber-600',
    outline: 'outline-amber-300'
  }
};
