import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Volume2, Home, ChevronLeft, ChevronRight } from 'lucide-react';
import WaveRecorder from './components/WaveRecorder';
import PromptCardMPT from './components/PromptCardMPT';
import { useTTS } from '@/hooks/useTTS';
import { toast } from 'sonner';
import { 
  createVocalSession, 
  submitVocalItem, 
  getVocalSession,
  type VocalSessionResponse 
} from '@/api/voice-training';

const MPTPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const attempt = parseInt(searchParams.get('attempt') || '1', 10);
  const sessionIdParam = searchParams.get('sessionId');
  
  const [blob, setBlob] = useState<Blob | null>(null);
  const [url, setUrl] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [sessionId, setSessionId] = useState<number | null>(
    sessionIdParam ? parseInt(sessionIdParam) : null
  );
  const [session, setSession] = useState<VocalSessionResponse | null>(null);
  const [isCompleted, setIsCompleted] = useState(false);
  
  const { supported, ready, speak } = useTTS('ko-KR');

  // 세션 생성 (첫 시도일 때)
  useEffect(() => {
    const initSession = async () => {
      if (attempt === 1 && !sessionId) {
        try {
          // 오늘 날짜를 YYYY-MM-DD 형식으로
          const today = new Date().toISOString().split('T')[0];
          
          const newSession = await createVocalSession({
            session_name: '발성 연습',
            type: 'vocal',
            item_count: 15, // 5가지 훈련 × 3회
            training_date: today,
            session_metadata: {
              training_types: ['MPT', 'crescendo', 'decrescendo', 'loud_soft', 'soft_loud']
            }
          });
          setSessionId(newSession.id);
          setSession(newSession);
          // URL에 sessionId 추가
          navigate(`/voice-training/mpt?attempt=1&sessionId=${newSession.id}`, { replace: true });
          toast.success('발성 훈련 세션이 생성되었습니다!');
        } catch (error) {
          console.error('세션 생성 실패:', error);
          toast.error('세션 생성에 실패했습니다.');
        }
      } else if (sessionId) {
        // 기존 세션 조회
        try {
          const existingSession = await getVocalSession(sessionId);
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

  const handleSubmit = async (audioBlob: Blob) => {
    if (!sessionId) {
      toast.error('세션 정보가 없습니다.');
      return;
    }

    setIsSubmitting(true);
    try {
      // 임시 그래프 이미지 생성 (실제로는 캔버스에서 생성)
      const graphImage = new File([audioBlob], 'graph.png', { type: 'image/png' });
      
      // MPT는 item_index 0, 1, 2 (attempt - 1)
      const itemIndex = attempt - 1;
      
      const result = await submitVocalItem({
        sessionId,
        itemIndex,
        audioFile: new File([audioBlob], 'audio.wav', { type: 'audio/wav' }),
        graphImage,
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
        const currentItem = result.session.training_items.find(item => item.item_index === itemIndex);
        
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
      // 같은 훈련 다음 시도
      navigate(`/voice-training/mpt?attempt=${attempt + 1}&sessionId=${sessionId}`);
      setBlob(null);
      setUrl('');
      setIsCompleted(false);
    } else {
      // 다음 훈련으로
      navigate(`/voice-training/crescendo?attempt=1&sessionId=${sessionId}`);
    }
  };

  const handlePrev = () => {
    if (attempt > 1) {
      navigate(`/voice-training/mpt?attempt=${attempt - 1}&sessionId=${sessionId}`);
    } else {
      navigate('/voice-training');
    }
  };

  return (
    <div className="w-full min-h-[calc(100vh-96px)] p-4 sm:p-8">
      <div className="max-w-4xl mx-auto">
        <Card>
          <CardContent className="p-6 sm:p-8">
            {/* 프롬프트 카드 */}
            <PromptCardMPT 
              main="아" 
              subtitle={`최대 발성 지속 시간 훈련 (MPT) - ${attempt}/3회`}
            />

            {/* 컨트롤 버튼들 */}
            <div className="flex flex-wrap gap-3 mb-8">
              <Button
                variant="outline"
                size="lg"
                disabled={!supported || !ready}
                onClick={handlePlayGuide}
                className="px-6 py-4 text-lg font-semibold flex items-center gap-2 hover:bg-blue-50 hover:border-blue-300"
              >
                <Volume2 className="w-6 h-6" strokeWidth={2.5} />
                안내 듣기
              </Button>
              
              <Button
                variant="outline"
                size="lg"
                onClick={handlePrev}
                className="px-6 py-4 text-lg font-semibold flex items-center gap-2"
              >
                <ChevronLeft className="w-6 h-6" strokeWidth={2.5} />
                {attempt > 1 ? '이전 시도' : '소개로'}
              </Button>

              <Button
                variant="ghost"
                size="lg"
                onClick={() => navigate('/')}
                className="px-6 py-4 text-lg font-semibold flex items-center gap-2 text-slate-600"
              >
                <Home className="w-6 h-6" strokeWidth={2.5} />
                홈
              </Button>
            </div>

            {/* 녹음 영역 */}
            <div className="mb-6">
              <WaveRecorder 
                onRecordEnd={handleRecordEnd} 
                onSubmit={handleSubmit}
                isSubmitting={isSubmitting}
              />
            </div>

            {/* 완료 상태 표시 */}
            {isCompleted && (
              <div className="mb-6 p-4 bg-green-50 rounded-xl border-2 border-green-200 text-center">
                <p className="text-lg font-bold text-green-700">
                  ✅ 훈련이 완료되었습니다! 다음으로 진행할 수 있습니다.
                </p>
              </div>
            )}

            {/* 다음 버튼 */}
            <div className="flex justify-center pt-4">
              <Button
                size="lg"
                onClick={handleNext}
                disabled={!isCompleted}
                className="min-w-[240px] px-8 py-6 text-xl bg-blue-500 hover:bg-blue-600 text-white font-semibold rounded-xl flex items-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed"
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

export default MPTPage;

