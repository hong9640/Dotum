import React from 'react';
import { Video, History } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Link } from 'react-router-dom';

const HomePage: React.FC = () => {
  return (
    <section className="w-full px-4 py-12 flex justify-center items-center">
      <div className="p-12 rounded-2xl flex flex-col items-center">
        {/* 상단 텍스트 및 이미지 영역 */}
        <div className="self-stretch pb-8 flex flex-col items-center gap-2.5">
          {/* 이미지 플레이스홀더 */}
          <div className="pb-6">
            <img
              className="w-52 h-48"
              src="https://placehold.co/204x198/e2e8f0/64748b?text=Image"
              alt="발음 교정 서비스"
            />
          </div>
          {/* 메인 헤딩 */}
          <div className="pb-4">
            <h1 className="text-center text-slate-800 text-5xl font-extrabold font-['Pretendard'] leading-[48px]">
              발음 교정 서비스
            </h1>
          </div>
          {/* 서브 헤딩 */}
          <div>
            <p className="text-center text-slate-600 text-2xl font-semibold font-['Pretendard'] leading-8">
              정상 발화 영상과 비교하며 발음을 교정해보세요.
            </p>
          </div>
        </div>

        {/* 하단 버튼 영역 */}
        <div className="flex flex-col sm:flex-row justify-center items-start gap-3.5">
          {/* 발음 연습 시작 버튼 (Primary) */}
          <Link to="/practice">
            <Button
              className="w-72 h-auto min-h-10 px-6 py-4 bg-green-500 text-white hover:bg-green-600 text-3xl font-semibold font-['Pretendard'] leading-9"
            >
              <Video className="w-8 h-8 mr-2" strokeWidth={2.5} />
              발음 연습 시작
            </Button>
          </Link>

          {/* 훈련 기록 버튼 (Outline) */}
          <Button
            variant="outline"
            className="w-72 h-auto min-h-10 px-6 py-4 bg-white text-slate-800 border-slate-200 border-2 hover:bg-slate-100 hover:text-slate-800 text-3xl font-semibold font-['Pretendard'] leading-9"
          >
            <History className="w-8 h-8 mr-2" strokeWidth={2.5} />
            훈련 기록
          </Button>
        </div>
      </div>
    </section>
  );
};

export default HomePage;
