import { ChevronLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface HeaderProps {
  date: string;
  totalSets: number;
  onBack?: () => void;
}

export function Header({ date, totalSets, onBack }: HeaderProps) {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  return (
    <div className="px-0 sm:px-8 pt-0 pb-7 sm:pt-7 relative w-full max-w-7xl mx-auto flex flex-col sm:inline-flex sm:justify-center items-start gap-2.5 max-w-[900px]">
      {/* 돌아가기 버튼 - sm 미만일 때는 일반 플로우, sm 이상일 때는 absolute */}
      <Button
        variant="ghost"
        className="px-0 md:px-0 py-2 md:py-3.5 sm:absolute sm:left-0 sm:top-4 md:top-[30px] rounded-lg flex justify-center items-center gap-2 md:gap-3 group transition-opacity hover:opacity-80 mb-4 sm:mb-0"
        onClick={onBack}
      >
        <ChevronLeft className="w-5 h-5 md:w-6 md:h-6 text-slate-500" strokeWidth={2.5} />
        <span className="justify-start text-slate-500 text-xl md:text-2xl font-normal leading-7 md:leading-9">
          돌아가기
        </span>
      </Button>
      <div className="w-full h-auto md:h-20 inline-flex flex-col justify-start items-center gap-2.5">
        {/* 제목 */}
        <div className="self-stretch px-4 inline-flex justify-center items-center gap-2.5">
          <h1 className="text-center justify-start text-slate-700 text-2xl md:text-4xl font-bold leading-tight md:leading-[48px]">
            {formatDate(date)}의 훈련 기록
          </h1>
        </div>
        {/* 날짜 */}
        <div className="self-stretch px-4 inline-flex justify-center items-center gap-2.5">
          <p className="text-center justify-start text-slate-500 text-base md:text-xl font-semibold leading-snug md:leading-7">
            총 {totalSets}개의 단어 세트를 연습했습니다.
          </p>
        </div>
      </div>
    </div>
  );
}
