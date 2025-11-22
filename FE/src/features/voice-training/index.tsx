import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/shared/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/card';
import { Volume2, TrendingUp, TrendingDown, Zap, Activity, ArrowRight } from 'lucide-react';

const VoiceTrainingIntro: React.FC = () => {
  const navigate = useNavigate();

  const trainings = [
    {
      id: 1,
      icon: Volume2,
      title: '최대 발성 지속 시간 연습 (MPT)',
      description: '편안하게 최대한 길게 발성하는 연습',
      color: 'bg-blue-100 border-blue-300 text-blue-800',
      iconColor: 'text-blue-700'
    },
    {
      id: 2,
      icon: TrendingUp,
      title: '크레셴도 연습 (점강)',
      description: '점점 크게 소리를 내는 연습',
      color: 'bg-teal-100 border-teal-300 text-teal-800',
      iconColor: 'text-teal-700'
    },
    {
      id: 3,
      icon: TrendingDown,
      title: '데크레셴도 연습 (점약)',
      description: '점점 작게 소리를 내는 연습',
      color: 'bg-yellow-100 border-yellow-300 text-yellow-800',
      iconColor: 'text-yellow-700'
    },
    {
      id: 4,
      icon: Zap,
      title: '순간 강약 전환 연습',
      description: '크게 시작해서 작게 끝나는 연습',
      color: 'bg-orange-100 border-orange-300 text-orange-800',
      iconColor: 'text-orange-700'
    },
    {
      id: 5,
      icon: Activity,
      title: '연속 강약 조절 연습',
      description: '작게 시작해서 크게 끝나는 연습',
      color: 'bg-pink-100 border-pink-300 text-pink-800',
      iconColor: 'text-pink-700'
    }
  ];

  const handleStart = () => {
    navigate('/voice-training/mpt?attempt=1');
  };

  return (
    <div className="w-full min-h-[calc(100vh-96px)] flex justify-center items-center p-4 sm:p-8">
      <div className="w-full max-w-4xl">
        <Card className="border-2">
          <CardHeader className="pb-4">
            <CardTitle className="text-center text-3xl sm:text-4xl font-extrabold text-slate-800 py-4">
              🎤 발성 연습 안내
            </CardTitle>
            <p className="text-center text-slate-600 text-lg sm:text-xl font-semibold">
              5가지 연습을 각각 1번씩 진행합니다
            </p>
          </CardHeader>

          <CardContent className="space-y-4">
            {/* 연습 순서 카드들 */}
            <div className="space-y-3">
              {trainings.map((training) => {
                const Icon = training.icon;
                return (
                  <Card
                    key={training.id}
                    className={`${training.color} border-2 transition-all hover:shadow-md`}
                  >
                    <CardContent className="p-4 sm:p-6">
                      <div className="flex items-center gap-4">
                        <div className="flex-shrink-0 w-12 h-12 sm:w-14 sm:h-14 rounded-full bg-white flex items-center justify-center">
                          <Icon className={`w-6 h-6 sm:w-7 sm:h-7 ${training.iconColor}`} strokeWidth={2.5} />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-lg sm:text-xl font-bold">{training.id}단계</span>
                            <h3 className="text-lg sm:text-xl font-bold truncate">
                              {training.title}
                            </h3>
                          </div>
                          <p className="text-sm sm:text-base">
                            {training.description}
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>

            {/* 안내 메시지 */}
            <Card className="bg-slate-50 border-slate-200">
              <CardContent className="p-4 sm:p-6">
                <div className="space-y-2 text-slate-700">
                  <p className="text-lg sm:text-xl font-semibold">📌 연습 방법</p>
                  <ul className="space-y-1 text-sm sm:text-lg ml-4">
                    <li>• 각 연습마다 1회씩 녹음합니다</li>
                    <li>• 녹음 버튼을 눌러 발성을 녹음해보세요</li>
                    <li>• 재녹음을 원하시면 다시 녹음할 수 있습니다</li>
                  </ul>
                </div>
              </CardContent>
            </Card>

            {/* 시작 버튼 */}
            <div className="flex justify-center pt-4">
              <Button
                size="lg"
                onClick={handleStart}
                className="w-[330px] sm:w-[400px] h-[68px] min-h-[40px] px-6 py-4 bg-green-500 rounded-xl flex justify-center items-center gap-3 hover:bg-green-600"
              >
                <span className="text-center text-white text-2xl lg:text-3xl font-semibold leading-9">
                  시작하기
                </span>
                <ArrowRight className="size-7 lg:size-9 text-white" strokeWidth={2.5} />
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default VoiceTrainingIntro;





