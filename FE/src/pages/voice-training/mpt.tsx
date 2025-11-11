import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Card, CardContent } from '@/components/ui/card';
import WaveRecorder from './components/WaveRecorder';
import PromptCardMPT from './components/PromptCardMPT';
import { toast } from 'sonner';
import {
  createTrainingSession,
  getTrainingSession,
  type CreateTrainingSessionResponse
} from '@/api/training-session';
import { submitVocalItem } from '@/api/voice-training';

const MPTPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const attempt = parseInt(searchParams.get('attempt') || '1', 10);
  const sessionIdParam = searchParams.get('sessionId');

  const [_blob, setBlob] = useState<Blob | null>(null);
  const [_url, setUrl] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [sessionId, setSessionId] = useState<number | null>(
    sessionIdParam ? parseInt(sessionIdParam) : null
  );
  const [_session, setSession] = useState<CreateTrainingSessionResponse | null>(null);
  const [resetTrigger, setResetTrigger] = useState(0);
  const promptCardRef = useRef<HTMLDivElement>(null);

  // 세션 생성 (첫 시도일 때)
  useEffect(() => {
    const initSession = async () => {
      if (attempt === 1 && !sessionId) {
        try {
          // 오늘 날짜를 YYYY-MM-DD 형식으로
          const today = new Date().toISOString().split('T')[0];

          const newSession = await createTrainingSession({
            session_name: '발성 연습',
            type: 'vocal',
            item_count: 15, // 5가지 훈련 × 3회
            training_date: today,
            session_metadata: {
              training_types: ['MPT', 'crescendo', 'decrescendo', 'loud_soft', 'soft_loud']
            }
          });
          setSessionId(newSession.session_id);
          setSession(newSession);
          // URL에 sessionId 추가
          navigate(`/voice-training/mpt?attempt=1&sessionId=${newSession.session_id}`, { replace: true });
        } catch (error) {
          console.error('세션 생성 실패:', error);
          toast.error('세션 생성에 실패했습니다.');
        }
      } else if (sessionId) {
        // 기존 세션 조회
        try {
          const existingSession = await getTrainingSession(sessionId);
          setSession(existingSession);
        } catch (error) {
          console.error('세션 조회 실패:', error);
        }
      }
    };

    initSession();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [attempt, sessionId]);

  // attempt가 변경될 때 리셋 트리거 증가 (첫 마운트 제외)
  const prevAttemptRef = React.useRef(attempt);
  useEffect(() => {
    if (prevAttemptRef.current !== attempt && prevAttemptRef.current > 0) {
      setResetTrigger(prev => prev + 1);
    }
    prevAttemptRef.current = attempt;
  }, [attempt]);

  // 페이지 진입 시 또는 attempt 변경 시 PromptCardMPT로 스크롤
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
      // MPT는 item_index 0, 1, 2 (attempt - 1)
      const itemIndex = attempt - 1;

      const result = await submitVocalItem({
        sessionId,
        itemIndex,
        audioFile: new File([audioBlob], `mpt_${attempt}.wav`, { type: 'audio/wav' }),
        graphImage: new File([graphImageBlob], `mpt_${attempt}_graph.png`, { type: 'image/png' }),
      });

      // 제출 완료 확인
      if (result.session) {
        setSession(result.session);
        const currentItem = result.session.training_items?.find((item: { item_index: number }) => item.item_index === itemIndex);
        
        if (currentItem?.is_completed) {
          // 제출 성공 후 자동으로 다음으로 이동
          if (attempt < 3) {
            // 같은 훈련 다음 시도
            setResetTrigger(prev => prev + 1);
            setTimeout(() => {
              navigate(`/voice-training/mpt?attempt=${attempt + 1}&sessionId=${sessionId}`);
              setIsSubmitting(false);  // ✅ navigate 후 로딩 해제
            }, 100);
          } else {
            // 다음 훈련으로
            setResetTrigger(prev => prev + 1);
            setTimeout(() => {
              navigate(`/voice-training/crescendo?attempt=1&sessionId=${sessionId}`);
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
        <div id="prompt-card-mpt" ref={promptCardRef}>
          <CardContent className="p-6 sm:p-8">
            {/* 프롬프트 카드 */}
              <PromptCardMPT
                main="아"
                subtitle="최대 발성 지속 시간 훈련"
                attempt={attempt}
                totalAttempts={3}
              />
            {/* 녹음 영역 */}
            <div className="mb-6">
              <WaveRecorder
                onRecordEnd={handleRecordEnd}
                onSubmit={handleSubmit}
                isSubmitting={isSubmitting}
                resetTrigger={resetTrigger}
              />
            </div>
          </CardContent>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default MPTPage;

