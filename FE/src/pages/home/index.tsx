import React from 'react';
import { BookOpen, ClipboardList, Languages, Smile } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';
import 도드미안경 from '@/assets/도드미_안경.png';
import { useTrainingSession } from '@/hooks/training-session';

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const { createWordSession, createSentenceSession, createVocalSession, isLoading, apiError } = useTrainingSession();

  const handleWordTraining = async () => {
    try {
      await createWordSession(2); // 2개 단어
    } catch (error) {
      console.error('단어 훈련 세션 생성 실패:', error);
    }
  };

  const handleSentenceTraining = async () => {
    try {
      await createSentenceSession(2); // 2개 문장
    } catch (error) {
      console.error('문장 훈련 세션 생성 실패:', error);
    }
  };

  const handleTrainingHistory = () => {
    navigate('/training-history');
  };

  const handleMaxVoiceTraining = () => {
    // 발성 훈련 페이지로 이동
    navigate('/voice-training');
  };

  return (
    <div className="w-full h-full min-h-100vh p-[49px] flex justify-center items-center">
      <div className="w-full max-w-7xl pt-0 sm:pt-12 pb-12 px-12 rounded-2xl flex flex-col lg:flex-row justify-center items-center sm:gap-7 gap-4 mx-1.5">
        {/* 에러 메시지 표시 */}
        {apiError && (
          <div className="fixed top-4 right-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded z-50">
            {apiError}
          </div>
        )}
        {/* 왼쪽 섹션 - 캐릭터 및 텍스트 */}
        <div className="w-full lg:w-auto pb-3 lg:pb-8 flex justify-center items-start">
          <div className="flex flex-col justify-start items-center gap-0.5 sm:gap-2.5">
            {/* 이미지 영역 */}
            <div className="pb-6 flex justify-center items-start">
              <img
                className="w-[204px] h-[198px]"
                src={도드미안경}
                alt="발음 교정 서비스"
              />
            </div>
            {/* 메인 헤딩 */}
            <div className="pb-2 flex justify-center items-start">
              <h1 className="text-center text-slate-800 text-3xl sm:text-4xl lg:text-5xl font-extrabold leading-tight">
                발음 교정 서비스
              </h1>
            </div>
            {/* 서브 헤딩 */}
            <div className="flex justify-center items-start">
              <p className="text-center text-slate-600 text-lg sm:text-xl lg:text-2xl font-semibold leading-8 whitespace-nowrap">
                정상 발화 영상과 비교하며 발음을 교정해보세요.
              </p>
            </div>
          </div>
        </div>

        {/* 오른쪽 섹션 - 버튼들 */}
        <div className="w-full lg:w-auto flex flex-col justify-start items-center gap-3.5">
          {/* 발성 연습 시작 버튼 */}
          <Button
            size="lg"
            onClick={handleMaxVoiceTraining}
            disabled={isLoading}
            className="w-[330px] sm:w-[400px] h-[68px] min-h-[40px] px-6 py-4 bg-lime-300 rounded-xl flex justify-center items-center gap-3 hover:bg-lime-400 disabled:opacity-50"
          >
            <Smile size={32} className="size-7 lg:size-9 text-white" strokeWidth={2.5} />
            <span className="text-center text-white text-2xl lg:text-3xl font-semibold leading-9">
              {isLoading ? "세션 생성 중..." : "발성 연습 시작"}
            </span>
          </Button>

          {/* 단어 연습 시작 버튼 */}
          <Button
            size="lg"
            onClick={handleWordTraining}
            disabled={isLoading}
            className="w-[330px] sm:w-[400px] h-[68px] min-h-[40px] px-6 py-4 bg-green-500 rounded-xl flex justify-center items-center gap-3 hover:bg-green-600 disabled:opacity-50"
          >
            <Languages size={32} className="size-7 lg:size-9 text-white" strokeWidth={2.5} />
            {/* <Languages size={32} className="hidden sm:block text-white" strokeWidth={2.5} /> */}
            <span className="text-center text-white text-2xl lg:text-3xl font-semibold leading-9">
              {isLoading ? "세션 생성 중..." : "단어 연습 시작"}
            </span>
          </Button>

          {/* 문장 연습 시작 버튼 */}
          <Button
            size="lg"
            onClick={handleSentenceTraining}
            disabled={isLoading}
            className="w-[330px] sm:w-[400px] h-[68px] min-h-[40px] px-6 py-4 bg-cyan-500 rounded-xl flex justify-center items-center gap-3 hover:bg-cyan-600 disabled:opacity-50"
          >
            <BookOpen size={32} className="size-7 lg:size-9 text-white" strokeWidth={2.5} />
            <span className="text-center text-white text-2xl lg:text-3xl font-semibold leading-9">
              {isLoading ? "세션 생성 중..." : "문장 연습 시작"}
            </span>
          </Button>

          {/* 훈련 기록 버튼 */}
          <Button
            variant="outline"
            size="lg"
            onClick={handleTrainingHistory}
            className="w-[330px] sm:w-[400px] h-[68px] min-h-[40px] px-6 py-4 bg-white rounded-xl outline outline-2 outline-slate-200 flex justify-center items-center gap-3 hover:bg-gray-100"
          >
            <ClipboardList size={32} className="size-7 lg:size-9 text-slate-800" strokeWidth={2.5} />
            <span className="text-center text-slate-800 text-2xl lg:text-3xl font-semibold leading-9">
              훈련 기록
            </span>
          </Button>
        </div>
      </div>
    </div>
  );
};

export default HomePage;
