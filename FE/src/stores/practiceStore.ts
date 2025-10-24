import { create } from 'zustand';

interface PracticeStore {
  // 현재 상태
  currentStep: number;
  totalSteps: number;
  currentWord: string;
  words: string[];
  
  // 액션들
  setStep: (step: number) => void;
  nextStep: () => void;
  setWords: (words: string[]) => void;
  resetPractice: () => void;
  
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
    currentWord: words[0] || "사과"
  }),

  // 연습 초기화
  resetPractice: () => set({
    currentStep: 1,
    currentWord: get().words[0] || "사과",
    recordedVideos: []
  }),

  // 녹화 상태 관리
  setRecording: (isRecording) => set({ isRecording }),
  
  addRecordedVideo: (videoUrl) => set((state) => ({
    recordedVideos: [...state.recordedVideos, videoUrl]
  }))
}));
