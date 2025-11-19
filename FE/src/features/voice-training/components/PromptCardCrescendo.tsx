import React from 'react';
import { Volume2, VolumeX } from 'lucide-react';
import { Button } from '@/shared/components/ui/button';
import { useTTS } from '@/shared/hooks/useTTS';

interface PromptCardCrescendoProps {
  main: string;
  subtitle: string;
  attempt: number;
  totalAttempts: number;
  isRecording?: boolean;
}

const PromptCardCrescendo: React.FC<PromptCardCrescendoProps> = ({ main, subtitle, attempt, totalAttempts, isRecording = false }) => {
  const instructionText = "작은 소리에서 시작해서 점점 크게 발성해주세요";
  const fullText = "음성연습을 진행하겠습니다. 점점 크게 말해주세요";
  
  const { speak, stop, isSpeaking, isSupported } = useTTS({
    lang: 'ko-KR',
    rate: 0.9,
    pitch: 1.0,
    volume: 1.0,
  });

  const handleTTSClick = () => {
    if (isSpeaking) {
      stop();
    } else {
      speak(fullText);
    }
  };

  return (
    <div className="p-8 sm:p-10 bg-gradient-to-br from-teal-50 to-teal-100 rounded-2xl border-3 border-teal-300 shadow-sm mb-8 text-center">
      <div className="text-2xl sm:text-3xl font-bold text-teal-800 mb-4">
        {attempt}/{totalAttempts}
      </div>
      <div className="flex justify-center items-end gap-1 mb-4">
        {[...main].map((char, i) => {
          // 크레셴도: 작 → 중 → 크 → 더크 (32 → 48 → 64 → 80)
          const sizes = [32, 48, 64, 80];
          return (
            <span
              key={i}
              className="font-extrabold text-teal-900 transition-all"
              style={{
                fontSize: `${sizes[i]}px`,
                lineHeight: 1,
              }}
            >
              {char}
            </span>
          );
        })}
        <span className="font-extrabold text-teal-900" style={{ fontSize: '80px', lineHeight: 1 }}>
          —
        </span>
      </div>
      <p className="text-xl sm:text-2xl font-bold text-teal-800 mb-3">
        {subtitle}
      </p>
      <div className="inline-block px-4 py-2 bg-teal-200/50 rounded-lg mb-4">
        <p className="text-base sm:text-lg text-teal-700 font-semibold">
          {instructionText}
        </p>
      </div>
      
      {/* TTS 버튼 */}
      {isSupported && (
        <div className="flex justify-center mt-4">
          <Button
            variant="outline"
            size="lg"
            onClick={handleTTSClick}
            disabled={isSpeaking || isRecording}
            className={`
              h-12 px-6
              border-2 
              transition-all duration-200
              ${isSpeaking 
                ? 'bg-teal-500 border-teal-500 text-white cursor-not-allowed opacity-70' 
                : 'bg-white hover:bg-teal-50 border-teal-400 text-teal-700'
              }
              disabled:cursor-not-allowed disabled:opacity-70
            `}
          >
            {isSpeaking ? (
              <>
                <VolumeX className="mr-2 h-5 w-5" />
                <span className="text-base font-semibold">재생 중...</span>
              </>
            ) : (
              <>
                <Volume2 className="mr-2 h-5 w-5" />
                <span className="text-base font-semibold">안내 듣기</span>
              </>
            )}
          </Button>
        </div>
      )}
    </div>
  );
};

export default PromptCardCrescendo;

