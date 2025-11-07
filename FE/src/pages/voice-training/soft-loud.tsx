import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Card, CardContent } from '@/components/ui/card';
import WaveRecorder from './components/WaveRecorder';
import PromptCardSoftLoud from './components/PromptCardSoftLoud';
import { toast } from 'sonner';
import { 
  getTrainingSession,
  completeTrainingSession,
  type CreateTrainingSessionResponse 
} from '@/api/training-session';
import { submitVocalItem } from '@/api/voice-training';

const SoftLoudPage: React.FC = () => {
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
    toast.success('녹음이 완료되었습니다!');
  };

  const handleSubmit = async (audioBlob: Blob, graphImageBlob: Blob) => {
    if (!sessionId) {
      toast.error('세션 정보가 없습니다.');
      return;
    }

    setIsSubmitting(true);
    try {
      // Soft-Loud는 item_index 12, 13, 14 (attempt + 11)
      const itemIndex = attempt + 11;
      
      const result = await submitVocalItem({
        sessionId,
        itemIndex,
        audioFile: new File([audioBlob], `soft_loud_${attempt}.wav`, { type: 'audio/wav' }),
        graphImage: new File([graphImageBlob], `soft_loud_${attempt}_graph.png`, { type: 'image/png' }),
      });

      if (result.session) {
        setSession(result.session);
        const currentItem = result.session.training_items?.find((item: any) => item.item_index === itemIndex);
        
        if (currentItem?.is_completed) {
          // 제출 성공 후 자동으로 다음으로 이동
          if (attempt < 3) {
            // 같은 훈련 다음 시도
            toast.success('훈련이 완료되었습니다!');
            setResetTrigger(prev => prev + 1);
            setTimeout(() => {
              navigate(`/voice-training/soft-loud?attempt=${attempt + 1}&sessionId=${sessionId}`);
            }, 500);
          } else {
            // 마지막 시도(attempt 3)가 완료되면 세션 완료 처리 후 result-list로 이동
            try {
              await completeTrainingSession(sessionId);
              toast.success('모든 발성 훈련을 완료했습니다! 🎉');
              setResetTrigger(prev => prev + 1);
              setTimeout(() => {
                navigate(`/result-list?sessionId=${sessionId}&type=vocal`);
              }, 1000);
            } catch (error) {
              console.error('세션 완료 처리 실패:', error);
              toast.success('훈련이 완료되었습니다!');
              setResetTrigger(prev => prev + 1);
              setTimeout(() => {
                navigate(`/result-list?sessionId=${sessionId}&type=vocal`);
              }, 1000);
            }
          }
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



  return (
    <div className="w-full min-h-[calc(100vh-96px)] p-4 sm:p-8">
      <div className="max-w-4xl mx-auto">
        <Card className="border-0 shadow-none">
          <CardContent className="p-6 sm:p-8">
            <PromptCardSoftLoud 
              main="아아아아아" 
              subtitle="연속 강약 조절 훈련"
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

export default SoftLoudPage;

