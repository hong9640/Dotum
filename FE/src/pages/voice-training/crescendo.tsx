import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Card, CardContent } from '@/components/ui/card';
import WaveRecorder from './components/WaveRecorder';
import PromptCardCrescendo from './components/PromptCardCrescendo';
import { toast } from 'sonner';
import { 
  getTrainingSession,
  type CreateTrainingSessionResponse 
} from '@/api/training-session';
import { submitVocalItem } from '@/api/voice-training';

const CrescendoPage: React.FC = () => {
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
  const [resetTrigger, setResetTrigger] = useState(0);

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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

  // attempt가 변경될 때 리셋 트리거 증가 (첫 마운트 제외)
  const prevAttemptRef = React.useRef(attempt);
  useEffect(() => {
    if (prevAttemptRef.current !== attempt && prevAttemptRef.current > 0) {
      setResetTrigger(prev => prev + 1);
    }
    prevAttemptRef.current = attempt;
  }, [attempt]);

  const handleRecordEnd = (b: Blob, u: string) => {
    setBlob(b);
    setUrl(u);
  };

  const handleSubmit = async (audioBlob: Blob, graphImageBlob: Blob) => {
    if (!sessionId) {
      toast.error('세션 정보가 없습니다.');
      return;
    }

    setIsSubmitting(true);
    try {
      // Crescendo는 item_index 3, 4, 5 (attempt + 2)
      const itemIndex = attempt + 2;
      
      const result = await submitVocalItem({
        sessionId,
        itemIndex,
        audioFile: new File([audioBlob], `crescendo_${attempt}.wav`, { type: 'audio/wav' }),
        graphImage: new File([graphImageBlob], `crescendo_${attempt}_graph.png`, { type: 'image/png' }),
      });

      if (result.session) {
        setSession(result.session);
        const currentItem = result.session.training_items?.find((item: { item_index: number }) => item.item_index === itemIndex);
        
        if (currentItem?.is_completed) {
          // 제출 성공 후 자동으로 다음으로 이동
          if (attempt < 3) {
            // 같은 훈련 다음 시도
            setResetTrigger(prev => prev + 1);
            setTimeout(() => {
              navigate(`/voice-training/crescendo?attempt=${attempt + 1}&sessionId=${sessionId}`);
              setIsSubmitting(false);  // ✅ navigate 후 로딩 해제
            }, 100);
          } else {
            // 다음 훈련으로
            setResetTrigger(prev => prev + 1);
            setTimeout(() => {
              navigate(`/voice-training/decrescendo?attempt=1&sessionId=${sessionId}`);
              setIsSubmitting(false);  // ✅ navigate 후 로딩 해제
            }, 100);
          }
        } else {
          toast.error('훈련이 완료되지 않았습니다. 다시 시도해주세요.');
          setIsSubmitting(false);  // ✅ 에러 시에만 해제
        }
      }
    } catch (error: unknown) {
      console.error('제출 실패:', error);
      const axiosError = error as { response?: { data?: { detail?: string } } };
      toast.error(axiosError.response?.data?.detail || '제출에 실패했습니다.');
      setIsSubmitting(false);  // ✅ 에러 시에만 해제
    }
    // ❌ finally 제거
  };



  return (
    <div className="w-full min-h-[calc(100vh-96px)] p-4 sm:p-8">
      <div className="max-w-4xl mx-auto">
        <Card className="border-0 shadow-none">
          <CardContent className="p-6 sm:p-8">
            <PromptCardCrescendo 
              main="아아아아" 
              subtitle="크레셴도 훈련"
              attempt={attempt}
              totalAttempts={3}
            />

            <div className="mb-6">
              <WaveRecorder 
                onRecordEnd={handleRecordEnd}
                onSubmit={handleSubmit}
                isSubmitting={isSubmitting}
                resetTrigger={resetTrigger}
              />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default CrescendoPage;

