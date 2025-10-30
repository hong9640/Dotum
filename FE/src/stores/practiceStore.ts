import { create } from 'zustand';

interface PracticeStore {
  // 현재 상태
  currentStep: number;
  totalSteps: number;
  currentWord: string;
  words: string[];
  currentWordIndex: number; // 현재 단어의 인덱스 (0부터 시작)
  sessionId: string | null;
  sessionType: 'word' | 'sentence' | null;
  
  // 액션들
  setStep: (step: number) => void;
  nextStep: () => void;
  setWords: (words: string[]) => void;
  setSessionData: (sessionId: string, sessionType: 'word' | 'sentence', words: string[], totalItems: number, currentItemIndex: number) => void;
  resetPractice: () => void;
  goToNextWord: () => void; // 다음 단어로 이동
  goToPreviousWord: () => void; // 이전 단어로 이동
  
  // 녹화 관련 상태
  isRecording: boolean;
  recordedVideos: string[];
  setRecording: (isRecording: boolean) => void;
  addRecordedVideo: (videoUrl: string) => void;
}

export const usePracticeStore = create<PracticeStore>((set, get) => ({
  // 초기 상태
  currentStep: 1,
  totalSteps: 0,
  currentWord: "",
  words: [],
  currentWordIndex: 0,
  sessionId: null,
  sessionType: null,
  isRecording: false,
  recordedVideos: [],

  // 단계 관리
  setStep: (step) => set({ currentStep: step }),
  
  nextStep: () => set((state) => {
    const nextStep = Math.min(state.currentStep + 1, state.totalSteps);
    const nextWord = state.words[nextStep - 1] || state.currentWord;
    return { 
      currentStep: nextStep,
      currentWord: nextWord
    };
  }),

  // 단어 목록 설정
  setWords: (words) => set({ 
    words, 
    totalSteps: words.length,
    currentStep: 1,
    currentWord: words[0] || "",
    currentWordIndex: 0
  }),

  // 세션 데이터 설정 (서버에서 받은 데이터)
  setSessionData: (sessionId, sessionType, words, totalItems, currentItemIndex) => set({
    sessionId,
    sessionType,
    words,
    totalSteps: totalItems, // 세션 생성 API의 total_items 사용
    currentStep: currentItemIndex + 1, // item_index + 1 (0부터 시작하므로)
    currentWord: words[0] || "",
    currentWordIndex: currentItemIndex, // 현재 진행 중인 아이템 조회 API의 item_index 사용
    recordedVideos: []
  }),

  // 연습 초기화
  resetPractice: () => set({
    currentStep: 1,
    currentWord: get().words[0] || "",
    currentWordIndex: 0,
    recordedVideos: []
  }),

  // 다음 단어로 이동
  goToNextWord: () => set((state) => {
    const nextIndex = state.currentWordIndex + 1;
    if (nextIndex < state.words.length) {
      return {
        currentWordIndex: nextIndex,
        currentWord: state.words[nextIndex],
        currentStep: nextIndex + 1
      };
    }
    return state; // 마지막 단어인 경우 변경하지 않음
  }),

  // 이전 단어로 이동
  goToPreviousWord: () => set((state) => {
    const prevIndex = state.currentWordIndex - 1;
    if (prevIndex >= 0) {
      return {
        currentWordIndex: prevIndex,
        currentWord: state.words[prevIndex],
        currentStep: prevIndex + 1
      };
    }
    return state; // 첫 번째 단어인 경우 변경하지 않음
  }),

  // 녹화 상태 관리
  setRecording: (isRecording) => set({ isRecording }),
  
  addRecordedVideo: (videoUrl) => set((state) => ({
    recordedVideos: [...state.recordedVideos, videoUrl]
  }))
}));
