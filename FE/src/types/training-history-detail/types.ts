// 연습 세트 데이터 타입
export interface TrainingSet {
  id: string;
  title: string;
  score: number | null; // null은 진행중 상태
  words: string[]; // 실제 단어/문장 텍스트 배열
  completedAt: string | null; // ISO date string, null은 진행중
  sessionId: number; // API의 session_id
  type: 'word' | 'sentence' | 'vocal';
  status: 'completed' | 'in_progress';
  totalItems: number;
  completedItems?: number; // 완료된 아이템 수
  currentItemIndex?: number; // 현재 진행 중인 아이템 인덱스
  created_at?: string; // 생성 날짜
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
  },
  in_progress: {
    background: 'bg-gray-100',
    backgroundHover: 'hover:bg-slate-50',
    border: 'border-gray-300',
    text: 'text-gray-600',
    outline: 'outline-gray-300'
  }
};
