import React from 'react';
import { Volume2, VolumeX } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useTTS } from '@/hooks/useTTS';

interface PromptCardMPTProps {
  main: string;
  subtitle: string;
  attempt: number;
  totalAttempts: number;
  isRecording?: boolean;
}

const PromptCardMPT: React.FC<PromptCardMPTProps> = ({ main, subtitle, attempt, totalAttempts, isRecording = false }) => {
  const instructionText = "편안하게 최대한 길게 발성해주세요";
  const fullText = "음성훈련을 시작하겠습니다. 아 라고 길게 발음해주세요";
  
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
    <div className="p-8 sm:p-10 bg-gradient-to-br from-blue-50 to-blue-100 rounded-2xl border-3 border-blue-300 shadow-sm mb-8 text-center">
      <div className="text-xl sm:text-3xl font-bold text-blue-800 mb-4">
        {attempt}/{totalAttempts}
      </div>
      <h1 className="text-5xl sm:text-6xl lg:text-7xl font-extrabold text-blue-900 mb-4">
        {main}—
      </h1>
      <p className="text-lg sm:text-2xl font-bold text-blue-800 mb-3">
        {subtitle}
      </p>
      <div className="inline-block px-4 py-2 bg-blue-200/50 rounded-lg mb-4">
        <p className="text-base sm:text-lg text-blue-700 font-semibold">
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
                ? 'bg-blue-500 border-blue-500 text-white cursor-not-allowed opacity-70' 
                : 'bg-white hover:bg-blue-50 border-blue-400 text-blue-700'
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

export default PromptCardMPT;

