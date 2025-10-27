import { create } from 'zustand';

interface PracticeStore {
  // 현재 상태
  currentStep: number;
  totalSteps: number;
  currentWord: string;
  words: string[];
  currentWordIndex: number; // 현재 단어의 인덱스 (0부터 시작)
  
  // 액션들
  setStep: (step: number) => void;
  nextStep: () => void;
  setWords: (words: string[]) => void;
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
  totalSteps: 10,
  currentWord: "사과",
  words: ["사과", "바나나", "딸기", "포도", "오렌지", "수박", "참외", "복숭아", "자두", "체리"],
  currentWordIndex: 0,
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
    currentWord: words[0] || "사과",
    currentWordIndex: 0
  }),

  // 연습 초기화
  resetPractice: () => set({
    currentStep: 1,
    currentWord: get().words[0] || "사과",
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
