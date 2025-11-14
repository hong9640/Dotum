import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ResultHeader } from '@/pages/common';
import { ResultVideoDisplay } from '@/pages/result-detail/components';

const ResultDetailMockup: React.FC = () => {
  const navigate = useNavigate();

  // 목업 데이터
  const mockItemData = {
    word: '사과',
    overallSummary: "말의 흐름은 편안했지만, '사과'의 마지막 모음에서 입모양이 충분히 펼쳐지지 않아 '사가'처럼 들린 부분이 있었어요.",
    evaluations: [
      {
        id: 1,
        title: '모음 왜곡도',
        content: "'과'의 모음이 충분히 둥글게 만들어지지 않아 '가'처럼 들렸어요. 입술을 조금 더 둥글게 모아주면 모양이 더 또렷하게 잡힐 거예요."
      },
      {
        id: 2,
        title: '소리의 안정도',
        content: "전체적인 흐름은 괜찮았지만, 마지막 소리에서 살짝 흔들리는 순간이 있었어요."
      },
      {
        id: 3,
        title: '음성 일탈도',
        content: "끝소리가 단어의 목표 음과 조금 다르게 들렸어요. 마무리 부분을 천천히 닫아주면 전달이 더 선명해질 거예요."
      },
      {
        id: 4,
        title: '음성 건강지수',
        content: "말할 때 목에 힘이 들어가지 않고 자연스럽게 발성하신 게 잘 느껴졌어요."
      }
    ],
    improvements: [
      "'과' 소리를 낼 때 입술을 살짝 더 앞으로 모아주고, 혀의 위치를 조금 뒤쪽으로 둥글게 만들어보면 모음이 더 분명하게 들릴 거예요.",
      "발음이 바뀌는 마지막 부분은 천천히 입모양을 유지하면서 마무리해보면 소리가 흔들리지 않고 안정적으로 이어질 거예요."
    ]
  };

  const handleBack = () => {
    navigate('/mockup/result-list');
  };

  return (
    <div className="self-stretch pt-7 pb-10 flex flex-col justify-start items-center bg-white min-h-screen">
      {/* 헤더 */}
      <ResultHeader
        type="word"
        date="상세 피드백 결과"
        onBack={handleBack}
        title={mockItemData.word}
      />

      {/* 메인 콘텐츠 영역 */}
      <div className="p-4 md:p-8 flex flex-col justify-start items-center gap-8 w-full max-w-7xl mx-auto">
        
        {/* 영상 비교 컴포넌트 */}
        <ResultVideoDisplay 
          userVideoUrl={undefined}
          compositedVideoUrl={undefined}
          isLoadingCompositedVideo={false}
          compositedVideoError={null}
        />
        
        {/* 한 줄 요약 (Overall) */}
        <div className="w-full bg-gradient-to-br from-green-50 via-green-100 to-emerald-50 rounded-2xl outline outline-[3px] outline-offset-[-3px] outline-green-200 p-8">
          <div className="flex flex-col gap-4">
            <div className="flex items-center gap-3">
              <div className="w-2 h-8 bg-green-500 rounded-full"></div>
              <h2 className="text-slate-800 text-3xl font-bold">한 줄 요약</h2>
            </div>
            <p className="text-slate-700 text-2xl font-semibold leading-relaxed pl-5">
              {mockItemData.overallSummary}
            </p>
          </div>
        </div>

        {/* 4개 항목별 평가 */}
        <div className="w-full bg-white rounded-2xl outline outline-[2px] outline-offset-[-2px] outline-gray-200 p-8 shadow-lg">
          <div className="flex flex-col gap-6">
            <div className="flex items-center gap-3">
              <div className="w-2 h-8 bg-cyan-500 rounded-full"></div>
              <h2 className="text-slate-800 text-3xl font-bold">항목별 평가</h2>
            </div>
            
            <div className="grid grid-cols-1 gap-6 mt-4">
              {mockItemData.evaluations.map((evaluation, index) => (
                <div 
                  key={evaluation.id}
                  className="bg-gradient-to-r from-slate-50 to-gray-50 rounded-xl p-6 border-l-4 border-cyan-500"
                >
                  <div className="flex items-start gap-4">
                    <div className="flex-shrink-0 w-10 h-10 bg-cyan-500 rounded-full flex items-center justify-center text-white text-xl font-bold">
                      {index + 1}
                    </div>
                    <div className="flex-1">
                      <h3 className="text-slate-800 text-2xl font-bold mb-3">
                        {evaluation.title}
                      </h3>
                      <p className="text-slate-700 text-xl leading-relaxed">
                        {evaluation.content}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 개선 포인트 */}
        <div className="w-full bg-gradient-to-br from-amber-50 via-yellow-50 to-orange-50 rounded-2xl outline outline-[3px] outline-offset-[-3px] outline-amber-200 p-8">
          <div className="flex flex-col gap-6">
            <div className="flex items-center gap-3">
              <div className="w-2 h-8 bg-amber-500 rounded-full"></div>
              <h2 className="text-slate-800 text-3xl font-bold">개선 포인트</h2>
            </div>
            
            <div className="flex flex-col gap-4 pl-5">
              {mockItemData.improvements.map((improvement, index) => (
                <div key={index} className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-8 h-8 bg-amber-400 rounded-full flex items-center justify-center text-white text-lg font-bold mt-1">
                    ✓
                  </div>
                  <p className="flex-1 text-slate-700 text-xl leading-relaxed">
                    {improvement}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 돌아가기 버튼 */}
        <div className="w-full flex justify-center mt-8">
          <button
            onClick={handleBack}
            className="px-8 py-4 bg-green-500 text-white text-xl font-semibold rounded-xl hover:bg-green-600 transition-colors shadow-lg"
          >
            목록으로 돌아가기
          </button>
        </div>
      </div>
    </div>
  );
};

export default ResultDetailMockup;
