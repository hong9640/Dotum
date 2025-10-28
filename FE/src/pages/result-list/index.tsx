import React from 'react';
import { useNavigate } from 'react-router-dom';
import ResultHeader from './components/ResultHeader';
import AverageScoreCard from './components/AverageScoreCard';
import WordResultsList from './components/WordResultsList';
import ActionButtons from './components/ActionButtons';
import type { WordResult } from './types';

// 목업 데이터
const resultsData: WordResult[] = [
  { id: 1, word: "사과", feedback: "발음이 정확하고 입모양이 우수합니다.", score: 92 },
  { id: 2, word: "바나나", feedback: "전반적으로 좋으나 마지막 음절을 더 명확하게 해보세요.", score: 85 },
  { id: 3, word: "딸기", feedback: "자음 발음을 조금 더 강하게 해보세요.", score: 78 },
  { id: 4, word: "포도", feedback: "매우 정확한 발음입니다.", score: 94 },
  { id: 5, word: "수박", feedback: "좋은 발음이지만 속도를 조금 늦춰보세요.", score: 89 },
  { id: 6, word: "복숭아", feedback: "복합음절 연결이 자연스럽습니다.", score: 82 },
  { id: 7, word: "오렌지", feedback: "발음이 안정적이고 명확합니다.", score: 88 },
  { id: 8, word: "키위", feedback: "짧은 단어 발음이 정확합니다.", score: 91 },
  { id: 9, word: "망고", feedback: "입모양과 발성이 균형적입니다.", score: 86 },
  { id: 10, word: "체리", feedback: "전체적으로 우수한 발음입니다.", score: 85 },
];

const WordSetResults: React.FC = () => {
  const navigate = useNavigate();
  
  // 전체 평균 점수 계산
  const totalScore = Math.round(resultsData.reduce((acc, r) => acc + r.score, 0) / resultsData.length);
  const formattedDate = "2025년 1월 25일 오후 3:24 완료"; // 필요시 동적으로 생성

  const handleBack = () => {
    navigate(-1); // 이전 페이지로 돌아가기
  };

  const handleDetailClick = (result: WordResult) => {
    // TODO: 상세 결과 페이지로 이동
    console.log("상세 결과 보기:", result);
    navigate(`/result-detail/${result.id}`);
  };

  const handleRetry = () => {
    // TODO: 다시 연습하기 로직
    console.log("다시 연습하기");
    navigate('/practice');
  };

  const handleNewTraining = () => {
    // TODO: 새로운 훈련 시작 로직
    console.log("새로운 훈련 시작");
    navigate('/practice');
  };

  return (
    <div className="self-stretch pt-7 pb-10 flex flex-col justify-start items-center bg-slate-50 min-h-screen">
      
      {/* 헤더 */}
      <ResultHeader
        title="단어 세트 A 결과"
        date={formattedDate}
        onBack={handleBack}
      />

      {/* 메인 콘텐츠 영역 */}
      <div className="p-4 md:p-8 flex flex-col justify-start items-center gap-8 w-full">
        
        {/* 전체 평균 점수 카드 */}
        <AverageScoreCard
          totalScore={totalScore}
          feedback="아주 잘했어요. 조금만 더 연습하면 완벽해질 것 같아요."
        />
        
        {/* 단어별 결과 목록 */}
        <WordResultsList
          results={resultsData}
          onDetailClick={handleDetailClick}
        />
        
        {/* 다음 행동 버튼 */}
        <ActionButtons
          onRetry={handleRetry}
          onNewTraining={handleNewTraining}
        />
      </div>
    </div>
  );
};

export default WordSetResults;
