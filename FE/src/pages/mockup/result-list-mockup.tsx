import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ResultHeader } from '@/pages/common';
import WordResultsList from '../result-list/components/WordResultsList';
import ActionButtons from '../result-list/components/ActionButtons';
import MetricCard from '../result-list/components/MetricCard';
import type { WordResult } from '../result-list/types';
import 도드미치료사 from "@/assets/도드미_치료사.png";

const ResultListMockup: React.FC = () => {
  const navigate = useNavigate();

  // 목업 데이터
  const mockResultsData: WordResult[] = [
    {
      id: 1,
      word: '사과',
      feedback: "'과'의 모음이 충분히 둥글게 만들어지지 않아 '가'처럼 들렸어요.",
      score: 85,
    },
    {
      id: 2,
      word: '바나나',
      feedback: '전체적으로 안정적인 발음이었어요.',
      score: 92,
    },
    {
      id: 3,
      word: '포도',
      feedback: '입모양이 또렷하게 잡혀서 전달력이 좋았어요.',
      score: 88,
    },
    {
      id: 4,
      word: '수박',
      feedback: '말할 때의 안정감이 한층 좋아졌어요.',
      score: 90,
    },
    {
      id: 5,
      word: '딸기',
      feedback: '소리의 흐름이 자연스럽게 이어졌어요.',
      score: 87,
    },
  ];

  const mockVoiceMetrics = {
    cpp: 8.5,
    csid: 12.3,
  };

  const mockOverallFeedback = "오늘 연습에서는 소리의 흐름이 자연스럽게 이어지고, 말할 때의 안정감도 한층 좋아졌어요. 몇몇 단어에서는 발음 모양이 또렷하게 잡혀서 전달력이 잘 살아났어요. 앞으로도 지금처럼 차분하게 이어가면 목소리가 더 편안하게 들릴 거예요.";

  const handleBack = () => {
    navigate('/');
  };

  const handleDetailClick = (result: WordResult) => {
    // 첫번째 아이템만 목업 상세 페이지로 이동
    if (result.id === 1) {
      navigate('/mockup/result-detail');
    } else {
      alert('목업은 첫번째 아이템만 지원합니다.');
    }
  };

  const handleRetry = () => {
    alert('재연습 기능 (목업)');
  };

  const handleNewTraining = () => {
    alert('새로운 연습 시작 (목업)');
  };

  return (
    <div className="self-stretch pt-7 pb-10 flex flex-col justify-start items-center bg-white min-h-screen">
      {/* 헤더 */}
      <ResultHeader
        type="word"
        date="2025년 11월 14일 오후 2:30"
        onBack={handleBack}
      />

      {/* 메인 콘텐츠 영역 */}
      <div className="p-4 md:p-8 flex flex-col justify-start items-center gap-8 w-full">
        
        {/* CPP/CSID 메트릭 카드 */}
        <div className="w-full max-w-[1220px] bg-gradient-to-br from-green-50 via-green-300 to-yellow-100 rounded-2xl outline outline-[3px] outline-offset-[-3px] outline-green-200 inline-flex flex-col md:flex-row justify-start items-stretch overflow-hidden">
          <div className="p-6 flex flex-col md:flex-row justify-start items-center gap-6 w-full min-w-0">
            
            {/* 이미지 래퍼 */}
            <div className="w-full md:flex-[0_0_28%] lg:flex-[0_0_32%] xl:flex-[0_0_34%] md:max-w-[340px] lg:max-w-[380px] xl:max-w-[420px] flex justify-center md:justify-start">
              <img 
                src={도드미치료사} 
                alt="결과 축하 이미지"
                className="w-full h-auto p-2.5 object-contain rounded-lg max-w-[340px] md:max-w-[380px] lg:max-w-[420px] max-h-[45vh] min-w-[358px] flex-shrink-0" 
              />
            </div>

            {/* 메트릭 카드 */}
            <div className="p-8 bg-white rounded-2xl shadow-lg inline-flex flex-col justify-start items-start gap-3.5 flex-1 min-w-0">
              <div className="w-full flex flex-col justify-start items-stretch gap-4">
                <MetricCard title="CPP" value={mockVoiceMetrics.cpp} normalRange="0" />
                <MetricCard title="CSID" value={mockVoiceMetrics.csid} normalRange="0" />
              </div>

              {/* 전체 피드백 메시지 */}
              <div className="self-stretch p-6 bg-green-50 rounded-2xl flex flex-col justify-start items-start mt-4">
                <div className="self-stretch inline-flex justify-start items-center gap-2.5">
                  <div className="justify-start text-slate-700 text-2xl font-semibold leading-8">
                    {mockOverallFeedback}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        {/* 단어별 결과 목록 */}
        <WordResultsList
          results={mockResultsData}
          onDetailClick={handleDetailClick}
          sessionType="word"
        />
        
        {/* 다음 행동 버튼 */}
        <ActionButtons
          onRetry={handleRetry}
          onNewTraining={handleNewTraining}
          isRetrying={false}
          isLoading={false}
        />
      </div>
    </div>
  );
};

export default ResultListMockup;
