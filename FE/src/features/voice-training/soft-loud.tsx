import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Card, CardContent } from '@/shared/components/ui/card';
import WaveRecorder from './components/WaveRecorder';
import PromptCardSoftLoud from './components/PromptCardSoftLoud';
import { toast } from 'sonner';
import {
  getTrainingSession,
  completeTrainingSession,
  type CreateTrainingSessionResponse
} from '@/features/training-session/api';
import { submitVocalItem } from '@features/voice-training/api';
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
  const [isRecording, setIsRecording] = useState(false);

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
    // 이미 제출 중이면 중복 실행 방지
    if (isSubmitting) return;

    if (!sessionId) {
      toast.error('세션 정보가 없습니다.');
      return;
    }

    setIsSubmitting(true);
    try {
      // Soft-Loud는 item_index 4
      const itemIndex = 4;

      const result = await submitVocalItem({
        sessionId,
        itemIndex,
        audioFile: new File([audioBlob], `soft_loud_${attempt}.wav`, { type: 'audio/wav' }),
        graphImage: new File([graphImageBlob], `soft_loud_${attempt}_graph.png`, { type: 'image/png' }),
      });

      if (result.session) {
        setSession(result.session);
        const currentItem = result.session.training_items?.find((item: { item_index: number }) => item.item_index === itemIndex);

        if (currentItem?.is_completed) {
          // 제출 성공 후 자동으로 다음으로 이동
          // 마지막 시도(attempt 1)가 완료되면 세션 완료 처리 후 result-list로 이동
          // ⚠️ setIsSubmitting(false)를 호출하지 않음 → 로딩 화면 유지
          try {
            await completeTrainingSession(sessionId);
            toast.success('모든 발성 연습을 완료했습니다! 🎉');
            setResetTrigger(prev => prev + 1);
            // ✅ setTimeout 제거 - 바로 이동
            navigate(`/result-list?sessionId=${sessionId}&type=vocal`);
            // 페이지 이동 후 언마운트되므로 setIsSubmitting 불필요
          } catch (error: unknown) {
            console.error('세션 완료 처리 실패:', error);
            setResetTrigger(prev => prev + 1);
            // ✅ setTimeout 제거 - 바로 이동
            navigate(`/result-list?sessionId=${sessionId}&type=vocal`);
            // 페이지 이동 후 언마운트되므로 setIsSubmitting 불필요
          }
        } else {
          toast.error('연습이 완료되지 않았습니다. 다시 시도해주세요.');
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
          <CardContent className="p-6 sm:p-8">
            <PromptCardSoftLoud
              main="아아아아아"
              subtitle="연속 강약 조절 연습"
              attempt={attempt}
              totalAttempts={1}
              isRecording={isRecording}
            />

            <div className="mb-6">
              <WaveRecorder
                onRecordEnd={handleRecordEnd}
                onSubmit={handleSubmit}
                isSubmitting={isSubmitting}
                isLastSubmit={attempt === 1}
                resetTrigger={resetTrigger}
                onRecordingStateChange={setIsRecording}
              />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default SoftLoudPage;

