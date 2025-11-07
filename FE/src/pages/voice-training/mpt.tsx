import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Card, CardContent } from '@/components/ui/card';
import WaveRecorder from './components/WaveRecorder';
import PromptCardMPT from './components/PromptCardMPT';
import { useTTS } from '@/hooks/useTTS';
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
  
  const { supported: _supported, ready: _ready, speak } = useTTS('ko-KR');

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
          toast.success('발성 훈련 세션이 생성되었습니다!');
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
  }, [attempt, sessionId]);

  const handleRecordEnd = (b: Blob, u: string) => {
    setBlob(b);
    setUrl(u);
    toast.success('녹음이 완료되었습니다!');
  };

  const handlePlayGuide = () => {
    speak('최대 발성 지속 시간 훈련을 시작하겠습니다. "아"라고 최대한 길게 발성해주세요.', {
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
      // MPT는 item_index 0, 1, 2 (attempt - 1)
      const itemIndex = attempt - 1;
      
      const result = await submitVocalItem({
        sessionId,
        itemIndex,
        audioFile: new File([audioBlob], `mpt_${attempt}.wav`, { type: 'audio/wav' }),
        graphImage: new File([graphImageBlob], `mpt_${attempt}_graph.png`, { type: 'image/png' }),
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            console.log(`업로드 진행률: ${percentCompleted}%`);
          }
        }
      });

      // 제출 완료 확인
      if (result.session) {
        setSession(result.session);
        const currentItem = result.session.training_items?.find((item: any) => item.item_index === itemIndex);
        
        if (currentItem?.is_completed) {
          toast.success('훈련이 완료되었습니다!');
          
          // 제출 성공 후 자동으로 다음으로 이동
          if (attempt < 3) {
            // 같은 훈련 다음 시도
            setResetTrigger(prev => prev + 1);
            setTimeout(() => {
              navigate(`/voice-training/mpt?attempt=${attempt + 1}&sessionId=${sessionId}`);
            }, 500);
          } else {
            // 다음 훈련으로
            setResetTrigger(prev => prev + 1);
            setTimeout(() => {
              navigate(`/voice-training/crescendo?attempt=1&sessionId=${sessionId}`);
            }, 500);
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
            {/* 프롬프트 카드 */}
            <PromptCardMPT 
              main="아" 
              subtitle={`최대 발성 지속 시간 훈련 (MPT) - ${attempt}/3회`}
              onPlayGuide={handlePlayGuide}
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
        </Card>
      </div>
    </div>
  );
};

export default MPTPage;

