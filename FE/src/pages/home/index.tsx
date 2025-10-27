import React from 'react';
import { PlayIcon, ClipboardList } from 'lucide-react';
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
              src="./src/assets/도드미_안경.png"
              alt="발음 교정 서비스"
            />
          </div>
          {/* 메인 헤딩 */}
          <div className="pb-4">
            <h1 className="text-center text-slate-800 text-5xl font-extrabold">
              발음 교정 서비스
            </h1>
          </div>
          {/* 서브 헤딩 */}
          <div>
            <p className="text-center text-slate-600 text-2xl font-semibold">
              정상 발화 영상과 비교하며 발음을 교정해보세요.
            </p>
          </div>
        </div>

        {/* 하단 버튼 영역 */}
        <div className="flex flex-col sm:flex-row justify-center items-start gap-3.5">
          {/* 발음 연습 시작 버튼 (Primary) */}
          <Link to="/practice">
            <Button
              size="lg"
              className="w-72 bg-green-500 text-white hover:bg-green-600"
            >
              <PlayIcon size={32} className="mr-2" strokeWidth={2.5} />
              발음 연습 시작
            </Button>
          </Link>

          {/* 훈련 기록 버튼 (Outline) */}
          <Link to="/training-history">
            <Button
              variant="outline"
              size="lg"
              className="w-72 bg-white text-gray-800 border-slate-200 border-2 hover:bg-gray-100 hover:text-gray-800"
            >
              <ClipboardList size={32} className="mr-2" strokeWidth={2.5} />
              훈련 기록
            </Button>
          </Link>
        </div>
      </div>
    </section>
  );
};

export default HomePage;
