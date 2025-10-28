import React from 'react';
import { useNavigate } from 'react-router-dom';
import ResultHeader from './components/ResultHeader';
import AverageScoreCard from './components/AverageScoreCard';
import WordResultsList from './components/WordResultsList';
import ActionButtons from './components/ActionButtons';
import type { WordResult } from './types';

// TODO: 실제 서버에서 받은 결과 데이터를 사용해야 함
// 현재는 빈 배열로 초기화 (실제 데이터는 서버에서 받아와야 함)
const resultsData: WordResult[] = [];

const WordSetResults: React.FC = () => {
  const navigate = useNavigate();
  
  // 전체 평균 점수 계산
  const totalScore = resultsData.length > 0 
    ? Math.round(resultsData.reduce((acc, r) => acc + r.score, 0) / resultsData.length)
    : 0;
  const formattedDate = "2025년 1월 25일 오후 3:24 완료"; // 필요시 동적으로 생성

  // 데이터가 없는 경우 처리
  if (resultsData.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-6">
          <div className="text-6xl mb-4">📊</div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">결과 데이터가 없습니다</h2>
          <p className="text-gray-600 mb-6">
            아직 완료된 훈련 결과가 없습니다.<br />
            훈련을 완료한 후 다시 확인해주세요.
          </p>
          <button 
            onClick={() => navigate('/')}
            className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            홈으로 돌아가기
          </button>
        </div>
      </div>
    );
  }

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
