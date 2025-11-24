import type { TrainingSet } from '@/features/training-history/types';
import type { DailyRecordSearchResponse } from '@/features/training-history/api/daily-record-search';

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
    completedAt: new Date(date).toISOString(),
    sessionId: index + 1,
    type: 'word' as const,
    status: 'completed' as const,
    totalItems: 10,
    completedItems: 10,
    currentItemIndex: 10
  }));
};

/**
 * API 응답을 TrainingSet 배열로 변환
 * 세션 타입별로 번호를 따로 매김
 */
export const convertSessionsToTrainingSets = (
  response: DailyRecordSearchResponse
): TrainingSet[] => {
  // 가장 오래된 것부터 1번이 되도록 역순으로 처리
  const sessions = [...response.sessions].reverse();

  // 타입별 카운터
  let wordCounter = 0;
  let sentenceCounter = 0;
  let vocalCounter = 0;

  return sessions.map((session) => {
    // 타입에 따라 카운터 증가 및 제목 생성
    // API에서 대문자로 오는 경우를 대비해 소문자로 변환하여 비교
    const sessionType = (session.type || '').toLowerCase();
    let title: string;

    if (sessionType === 'word') {
      wordCounter++;
      title = `단어 세트 ${wordCounter}`;
    } else if (sessionType === 'sentence') {
      sentenceCounter++;
      title = `문장 세트 ${sentenceCounter}`;
    } else if (sessionType === 'vocal') {
      vocalCounter++;
      title = `발성 연습 ${vocalCounter}`;
    } else {
      // 알 수 없는 타입의 경우 기본값
      sentenceCounter++;
      title = `문장 세트 ${sentenceCounter}`;
    }

    // 실제 단어/문장 텍스트 배열 생성 (최대 3개)
    const words: string[] = [];
    const items = session.training_items.slice(0, 3); // 최대 3개만

    items.forEach((item) => {
      if (item.word) {
        words.push(item.word);
      } else if (item.sentence) {
        words.push(item.sentence);
      }
    });

    // 점수 계산
    // API 상태가 completed이거나, 아이템을 모두 완료한 경우 완료된 것으로 판단
    const isAllItemsCompleted = session.total_items > 0 && session.total_items === session.completed_items;
    const isCompleted = session.status === 'completed' || isAllItemsCompleted;

    const score = isCompleted
      ? (session.average_score ?? 50) // average_score가 있으면 사용, 없으면 임시로 50점
      : null;

    return {
      id: String(session.session_id),
      title: title,
      score,
      words: words,
      completedAt: session.completed_at,
      sessionId: session.session_id,
      type: sessionType as 'word' | 'sentence' | 'vocal',
      status: session.status,
      totalItems: session.total_items,
      completedItems: session.completed_items,
      currentItemIndex: session.current_item_index,
      created_at: session.created_at
    };
  });
};
