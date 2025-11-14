import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Card, CardContent } from '@/components/ui/card';
import WaveRecorder from './components/WaveRecorder';
import PromptCardDecrescendo from './components/PromptCardDecrescendo';
import { toast } from 'sonner';
import {
  getTrainingSession,
  type CreateTrainingSessionResponse
} from '@/api/trainingSession';
import { submitVocalItem } from '@/api/voiceTraining';

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
  const [resetTrigger, setResetTrigger] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const promptCardRef = useRef<HTMLDivElement>(null);

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

  // 페이지 진입 시 또는 attempt 변경 시 PromptCardDecrescendo로 스크롤
  useEffect(() => {
    if (promptCardRef.current) {
      promptCardRef.current.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'start' 
      });
    }
  }, [attempt]);

  const handleRecordEnd = (b: Blob, u: string) => {
    setBlob(b);
    setUrl(u);
  };

  const handleSubmit = async (audioBlob: Blob, graphImageBlob: Blob) => {
    // 이미 제출 중이면 중복 실행 방지
    if (isSubmitting) return;
    
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
        const currentItem = result.session.training_items?.find((item: { item_index: number }) => item.item_index === itemIndex);
        
        if (currentItem?.is_completed) {
          // 제출 성공 후 자동으로 다음으로 이동
          if (attempt < 3) {
            // 같은 훈련 다음 시도
            setResetTrigger(prev => prev + 1);
            setTimeout(() => {
              navigate(`/voice-training/decrescendo?attempt=${attempt + 1}&sessionId=${sessionId}`);
              setIsSubmitting(false);  // ✅ navigate 후 로딩 해제
            }, 100);
          } else {
            // 다음 훈련으로
            setResetTrigger(prev => prev + 1);
            setTimeout(() => {
              navigate(`/voice-training/loud-soft?attempt=1&sessionId=${sessionId}`);
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
      
      const axiosError = error as { response?: { status?: number; data?: { detail?: string } } };
      const status = axiosError.response?.status;
      
      // 401: 인증 오류 - 강제 로그인 페이지 이동
      if (status === 401) {
        toast.error('세션이 만료되었습니다. 다시 로그인해주세요.');
        setIsSubmitting(false);
        setTimeout(() => navigate('/login'), 1500);
        return;
      }
      
      // 404: 세션 없음 - 강제 홈으로 이동
      if (status === 404) {
        toast.error('세션을 찾을 수 없습니다. 홈에서 다시 시작해주세요.');
        setIsSubmitting(false);
        setTimeout(() => navigate('/'), 1500);
        return;
      }
      
      // 422: 파일 오류 - 새로고침 권장
      if (status === 422) {
        toast.error('파일이 올바르지 않습니다. 페이지를 새로고침해주세요.');
        setIsSubmitting(false);
        return;
      }
      
      // 그 외 에러
      toast.error(axiosError.response?.data?.detail || '제출에 실패했습니다.');
      setIsSubmitting(false);
    }
  };



  return (
    <div className="w-full min-h-[calc(100vh-96px)] p-4 sm:p-8">
      <div className="max-w-4xl mx-auto">
        <Card className="border-0 shadow-none">
          <div id="prompt-card-decrescendo" ref={promptCardRef}>
            <CardContent className="p-6 sm:p-8">
              <PromptCardDecrescendo
                main="아아아아"
                subtitle="데크레셴도 훈련"
                attempt={attempt}
                totalAttempts={3}
                isRecording={isRecording}
              />

            <div className="mb-6">
              <WaveRecorder
                onRecordEnd={handleRecordEnd}
                onSubmit={handleSubmit}
                isSubmitting={isSubmitting}
                resetTrigger={resetTrigger}
                onRecordingStateChange={setIsRecording}
              />
            </div>
            </CardContent>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default DecrescendoPage;

