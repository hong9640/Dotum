import React from 'react';
import { Volume2, VolumeX } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useTTS } from '@/hooks/shared/useTTS';

interface PromptCardLoudSoftProps {
  main: string;
  subtitle: string;
  attempt: number;
  totalAttempts: number;
  isRecording?: boolean;
}

const PromptCardLoudSoft: React.FC<PromptCardLoudSoftProps> = ({ main, subtitle, attempt, totalAttempts, isRecording = false }) => {
  // 크게 → 약간 작게 → 작게 → 약간 작게 → 크게 (가운데 대칭: 80 → 56 → 32 → 56 → 80)
  const sizes = [80, 56, 32, 56, 80];
  const fullText = "음성훈련을 진행하겠습니다. 그림에 따라 점점 크게 말하다 작게 말해주세요";
  
  const { speak, stop, isSpeaking, isSupported } = useTTS({
    lang: 'ko-KR',
    rate: 0.85,
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
    <div className="p-8 sm:p-10 bg-gradient-to-br from-orange-50 to-orange-100 rounded-2xl border-3 border-orange-300 shadow-sm mb-8 text-center">
      <div className="text-2xl sm:text-3xl font-bold text-orange-800 mb-4">
        {attempt}/{totalAttempts}
      </div>
      <div className="flex justify-center items-end gap-1 mb-4">
        {[...main].map((char, i) => (
          <span
            key={i}
            className="font-extrabold text-orange-900 transition-all"
            style={{
              fontSize: `${sizes[i]}px`,
              lineHeight: 1,
            }}
          >
            {char}
          </span>
        ))}
        <span className="font-extrabold text-orange-900" style={{ fontSize: '80px', lineHeight: 1 }}>
          —
        </span>
      </div>
      <p className="text-xl sm:text-2xl font-bold text-orange-800 mb-3">
        {subtitle}
      </p>
      <div className="inline-block px-4 py-2 bg-orange-200/50 rounded-lg mb-4">
        <p className="text-base sm:text-lg text-orange-700 font-semibold">
          크게 → 약간 작게 → 작게 → 약간 작게 → 크게 변화를 주며 발성해주세요
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
                ? 'bg-orange-500 border-orange-500 text-white cursor-not-allowed opacity-70' 
                : 'bg-white hover:bg-orange-50 border-orange-400 text-orange-700'
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

export default PromptCardLoudSoft;

