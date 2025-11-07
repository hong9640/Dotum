import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { ChevronRight } from 'lucide-react';
import WaveRecorder from './components/WaveRecorder';
import PromptCardDecrescendo from './components/PromptCardDecrescendo';
import { useTTS } from '@/hooks/useTTS';
import { toast } from 'sonner';
import { 
  getTrainingSession,
  type CreateTrainingSessionResponse 
} from '@/api/training-session';
import { submitVocalItem } from '@/api/voice-training';

const DecrescendoPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const attempt = parseInt(searchParams.get('attempt') || '1', 10);
  const sessionIdParam = searchParams.get('sessionId');
  
  const [_blob, setBlob] = useState<Blob | null>(null);
  const [_url, setUrl] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [sessionId, _setSessionId] = useState<number | null>(
    sessionIdParam ? parseInt(sessionIdParam) : null
  );
  const [_session, setSession] = useState<CreateTrainingSessionResponse | null>(null);
  const [isCompleted, setIsCompleted] = useState(false);
  
  const { supported: _supported, ready: _ready, speak } = useTTS('ko-KR');

  useEffect(() => {
    const loadSession = async () => {
      if (sessionId) {
        try {
          const existingSession = await getTrainingSession(sessionId);
          setSession(existingSession);
        } catch (error) {
          console.error('세션 조회 실패:', error);
          toast.error('세션 정보를 불러올 수 없습니다.');
          navigate('/voice-training/mpt?attempt=1');
        }
      } else {
        toast.error('세션 정보가 없습니다.');
        navigate('/voice-training/mpt?attempt=1');
      }
    };

    loadSession();
  }, [sessionId]);

  const handleRecordEnd = (b: Blob, u: string) => {
    setBlob(b);
    setUrl(u);
    toast.success('녹음이 완료되었습니다!');
  };

  const handlePlayGuide = () => {
    speak('데크레셴도 훈련을 시작하겠습니다. "아"라고 점점 작게 발성해주세요.', {
      rate: 1,
      pitch: 1.1,
      volume: 1,
    });
  };

  const handleSubmit = async (audioBlob: Blob, graphImageBlob: Blob) => {
    if (!sessionId) {
      toast.error('세션 정보가 없습니다.');
      return;
    }

    setIsSubmitting(true);
    try {
      // Decrescendo는 item_index 6, 7, 8 (attempt + 5)
      const itemIndex = attempt + 5;
      
      const result = await submitVocalItem({
        sessionId,
        itemIndex,
        audioFile: new File([audioBlob], `decrescendo_${attempt}.wav`, { type: 'audio/wav' }),
        graphImage: new File([graphImageBlob], `decrescendo_${attempt}_graph.png`, { type: 'image/png' }),
      });

      if (result.session) {
        setSession(result.session);
        const currentItem = result.session.training_items?.find((item: any) => item.item_index === itemIndex);
        
        if (currentItem?.is_completed) {
          setIsCompleted(true);
          toast.success('훈련이 완료되었습니다!');
        } else {
          toast.error('훈련이 완료되지 않았습니다. 다시 시도해주세요.');
        }
      }
    } catch (error: any) {
      console.error('제출 실패:', error);
      toast.error(error.response?.data?.detail || '제출에 실패했습니다.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleNext = () => {
    if (!isCompleted) {
      toast.error('먼저 훈련을 완료해주세요.');
      return;
    }

    if (attempt < 3) {
      navigate(`/voice-training/decrescendo?attempt=${attempt + 1}&sessionId=${sessionId}`);
      setBlob(null);
      setUrl('');
      setIsCompleted(false);
    } else {
      navigate(`/voice-training/loud-soft?attempt=1&sessionId=${sessionId}`);
    }
  };


  return (
    <div className="w-full min-h-[calc(100vh-96px)] p-4 sm:p-8">
      <div className="max-w-4xl mx-auto">
        <Card className="border-0 shadow-none">
          <CardContent className="p-6 sm:p-8">
            <PromptCardDecrescendo 
              main="아아아아아" 
              subtitle={`데크레셴도 훈련 (점약) - ${attempt}/3회`}
              onPlayGuide={handlePlayGuide}
            />

            <div className="mb-6">
              <WaveRecorder 
                onRecordEnd={handleRecordEnd}
                onSubmit={handleSubmit}
                isSubmitting={isSubmitting}
              />
            </div>

            {isCompleted && (
              <div className="mb-6 p-4 bg-yellow-50 rounded-xl border-2 border-yellow-200 text-center">
                <p className="text-lg font-bold text-yellow-700">
                  ✅ 훈련이 완료되었습니다! 다음으로 진행할 수 있습니다.
                </p>
              </div>
            )}

            <div className="flex justify-center pt-4">
              <Button
                size="lg"
                onClick={handleNext}
                disabled={!isCompleted}
                className="min-w-[240px] px-8 py-6 text-xl bg-yellow-500 hover:bg-yellow-600 text-white font-semibold rounded-xl flex items-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {attempt < 3 ? (
                  <>
                    다음 시도 ({attempt + 1}/3)
                    <ChevronRight className="w-6 h-6" strokeWidth={2.5} />
                  </>
                ) : (
                  <>
                    다음 훈련으로
                    <ChevronRight className="w-6 h-6" strokeWidth={2.5} />
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default DecrescendoPage;

