import type { WordResult } from '@/types/result-list';

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

/**
 * 세션 상세 조회 API 응답을 WordResult 배열로 변환하는 함수 (예시)
 * 
 * 현재는 word 또는 sentence 필드가 API 응답에 포함되어 있지 않아서
 * 더미데이터를 사용하고 있으나, 나중에 백엔드에서 word/sentence 정보를
 * 제공하면 아래 함수를 활성화하여 사용할 수 있습니다.
 * 
 * 사용 예시:
 * const sessionDetail = await getSessionDetail(sessionId);
 * const wordResults = convertSessionDetailToWordResults(sessionDetail);
 * 
 * @param sessionDetail 세션 상세 조회 API 응답 데이터
 * @returns WordResult 배열
 */
// import type { SessionDetailResponse } from '@/api/result-list/session-detail-search';
// export const convertSessionDetailToWordResults = (
//   sessionDetail: SessionDetailResponse
// ): WordResult[] => {
//   // completed_items만큼만 변환 (완료된 아이템만)
//   return sessionDetail.training_items
//     .filter(item => item.is_completed)
//     .slice(0, sessionDetail.completed_items)
//     .map((item, index) => {
//       // TODO: 백엔드에서 word 또는 sentence 필드를 제공하면 아래 로직 사용
//       // const wordText = item.word_id 
//       //   ? /* word_id로 단어 조회 API 호출하여 word 필드 가져오기 */
//       //   : item.sentence_id 
//       //   ? /* sentence_id로 문장 조회 API 호출하여 sentence 필드 가져오기 */
//       //   : '데이터 없음';
//       
//       // 현재는 word/sentence 정보가 없으므로 더미데이터 사용
//       const dummyWords = [
//         '사과', '바나나', '딸기', '포도', '오렌지',
//         '수박', '체리', '복숭아', '자두', '키위'
//       ];
//       const dummyFeedbacks = [
//         '아주 잘했어요!',
//         '좋은 발음이에요.',
//         '조금 더 연습이 필요해요.',
//         '훌륭합니다!',
//         '잘 하고 있어요.',
//       ];
//       const dummyScores = [95, 87, 75, 92, 88];
//       
//       return {
//         id: item.item_index + 1, // item_index는 0부터 시작하므로 +1
//         word: dummyWords[index % dummyWords.length], // TODO: 실제 word/sentence 필드 사용
//         feedback: dummyFeedbacks[index % dummyFeedbacks.length], // TODO: 실제 피드백 API 호출
//         score: dummyScores[index % dummyScores.length] // TODO: 실제 점수 API 호출
//       };
//     });
// };

