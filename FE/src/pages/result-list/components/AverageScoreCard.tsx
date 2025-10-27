import React from 'react';
import 도드미치료사 from "@/assets/도드미_치료사.png";

interface AverageScoreCardProps {
  totalScore: number;
  feedback: string;
  imageUrl?: string;
}

const AverageScoreCard: React.FC<AverageScoreCardProps> = ({ 
  totalScore, 
  feedback, 
  imageUrl = 도드미치료사
}) => {
  return (
    <div className="w-full max-w-[1220px] bg-gradient-to-br from-green-50 via-green-300 to-yellow-100 rounded-2xl outline outline-[3px] outline-offset-[-3px] outline-green-200 inline-flex flex-col md:flex-row justify-start items-start overflow-hidden">
      <div className="flex-1 p-6 flex flex-col md:flex-row justify-start items-center gap-6">
        <img 
          className="w-full md:w-60 h-auto md:self-stretch p-2.5 object-cover rounded-lg" 
          src={imageUrl} 
          alt="결과 축하 이미지" 
        />
        <div className="flex-1 p-8 bg-white rounded-2xl shadow-lg inline-flex flex-col justify-start items-start gap-3.5 w-full">
          <div className="self-stretch inline-flex justify-start items-center gap-2.5">
            <div className="justify-start text-slate-700 text-lg md:text-xl font-semibold leading-snug md:leading-7">
              전체 평균 점수
            </div>
          </div>
          <div className="self-stretch inline-flex justify-start items-center gap-2.5">
            <div 
              className="w-auto md:w-48 justify-start text-6xl md:text-7xl font-black leading-tight md:leading-[80px]"
              style={{
                background: 'linear-gradient(90deg, #3B82F6 0%, #4F46E5 42.21%, #6D28D9 84.42%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text'
              }}
            >
              {totalScore}점
            </div>
          </div>
          <div className="self-stretch p-6 bg-green-50 rounded-2xl flex flex-col justify-start items-start">
            <div className="self-stretch inline-flex justify-start items-center gap-2.5">
              <div className="justify-start text-slate-700 text-lg md:text-2xl font-semibold leading-snug md:leading-8">
                {feedback}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AverageScoreCard;
