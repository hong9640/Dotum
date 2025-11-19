// Video 관련
// 비디오 컴포넌트는 shared/components/media로 이동됨
export { ResultVideoDisplay } from '@/shared/components/media';

// Feedback 및 Evaluation 관련
// 결과 관련 컴포넌트는 shared/components/result로 이동됨
export { 
  FeedbackCard, 
  FeedbackSummary, 
  PronunciationScore, 
  ImprovementPoints,
  DetailedEvaluationItems,
  DetailedEvaluationItemCard
} from '@/shared/components/result';

// Types
export type { 
  FeedbackCardComponentProps as FeedbackCardProps,
  DetailedEvaluationItem, 
  EvaluationStatus 
} from '@/shared/components/result';



