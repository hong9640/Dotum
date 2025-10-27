import { ArrowLeft } from 'lucide-react';

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
    <div className="px-8 py-[30px] self-stretch">
      <div className="flex items-center justify-between mb-6">
        <div className="px-4 py-3.5 bg-white/0 rounded-lg flex justify-center items-center gap-3 cursor-pointer hover:bg-gray-50 transition-colors" onClick={onBack}>
          <ArrowLeft className="w-8 h-8 text-slate-500" />
          <div className="text-slate-500 text-3xl font-medium font-['Pretendard'] leading-9">돌아가기</div>
        </div>
        <div className="text-center text-slate-700 text-3xl font-semibold font-['Pretendard'] leading-9">
          {formatDate(date)}의 훈련 기록
        </div>
        <div className="w-[200px]"></div> {/* 돌아가기 버튼과 균형을 맞추기 위한 빈 공간 */}
      </div>
      <div className="text-center text-slate-500 text-xl font-semibold font-['Pretendard'] leading-7">
        총 {totalSets}개의 단어 세트를 연습했습니다.
      </div>
    </div>
  );
}
