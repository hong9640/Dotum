# 발성 연습 (Voice Training) 모듈

발음 교정 서비스 "돋음"의 발성 연습 기능 모듈입니다.

## 📁 디렉토리 구조

```
src/
├── hooks/
│   ├── useTTS.ts                  # TTS (음성 안내) Hook
│   └── useAudioRecorder.ts        # 오디오 녹음 Hook
│
├── pages/
│   └── voice-training/
│       ├── components/             # 발성 연습 전용 컴포넌트
│       │   ├── AudioPlayer.tsx         # 오디오 재생기
│       │   ├── AudioVisualizer.tsx     # 오디오 시각화 (주파수 스펙트럼)
│       │   ├── RecordToggle.tsx        # 녹음 버튼
│       │   ├── StatusBadge.tsx         # 상태 배지
│       │   ├── WaveRecorder.tsx        # 녹음기 메인 컴포넌트
│       │   ├── PromptCardMPT.tsx       # MPT 프롬프트 카드
│       │   ├── PromptCardCrescendo.tsx # 크레셴도 프롬프트 카드
│       │   ├── PromptCardDecrescendo.tsx # 데크레셴도 프롬프트 카드
│       │   ├── PromptCardLoudSoft.tsx  # 순간 강약 전환 프롬프트
│       │   └── PromptCardSoftLoud.tsx  # 연속 강약 조절 프롬프트
│       │
│       ├── index.tsx               # 발성 연습 소개 페이지
│       ├── mpt.tsx                 # 최대 발성 지속 시간 훈련 (MPT)
│       ├── crescendo.tsx           # 크레셴도 훈련 (점강)
│       ├── decrescendo.tsx         # 데크레셴도 훈련 (점약)
│       ├── loud-soft.tsx           # 순간 강약 전환 훈련
│       └── soft-loud.tsx           # 연속 강약 조절 훈련
│
└── api/
    └── voice-training/             # (향후 필요시 추가)
```

## 🎯 훈련 플로우

```
1. 소개 페이지 (/voice-training)
   - 5가지 훈련 순서 안내
   - 훈련 방법 설명
   ↓
2. MPT 훈련 (/voice-training/mpt?attempt=1~3)
   - 최대 발성 지속 시간 훈련
   - 3회 시도
   ↓
3. 크레셴도 훈련 (/voice-training/crescendo?attempt=1~3)
   - 점점 크게 발성
   - 3회 시도
   ↓
4. 데크레셴도 훈련 (/voice-training/decrescendo?attempt=1~3)
   - 점점 작게 발성
   - 3회 시도
   ↓
5. 순간 강약 전환 훈련 (/voice-training/loud-soft?attempt=1~3)
   - 크게 → 작게 변화
   - 3회 시도
   ↓
6. 연속 강약 조절 훈련 (/voice-training/soft-loud?attempt=1~3)
   - 작게 → 크게 변화
   - 3회 시도
   ↓
완료 → 홈으로 이동
```

## 🎨 주요 컴포넌트

### WaveRecorder
녹음 기능의 메인 컴포넌트입니다.

```tsx
import WaveRecorder from './components/WaveRecorder';

<WaveRecorder 
  onRecordEnd={(blob, url) => {
    // 녹음 완료 시 처리
  }} 
/>
```

**기능:**
- 마이크 권한 요청
- 오디오 녹음 (MediaRecorder API)
- 실시간 오디오 시각화
- 녹음 상태 표시
- 녹음 파일 재생

### AudioVisualizer
실시간 오디오 주파수 스펙트럼을 시각화합니다.

```tsx
import AudioVisualizer from './components/AudioVisualizer';

<AudioVisualizer 
  active={isRecording}
  stream={mediaStream}
  width={700}
  height={120}
/>
```

**기술:**
- Web Audio API
- Canvas 기반 렌더링
- requestAnimationFrame으로 부드러운 애니메이션

### Prompt Cards
각 훈련 타입별 시각적 안내 카드입니다.

- **PromptCardMPT**: 파란색, 일정한 크기
- **PromptCardCrescendo**: 노란색, 점점 커지는 텍스트
- **PromptCardDecrescendo**: 보라색, 점점 작아지는 텍스트
- **PromptCardLoudSoft**: 핑크색, 파동 형태
- **PromptCardSoftLoud**: 초록색, 역파동 형태

## 🎣 커스텀 Hooks

### useTTS
브라우저 네이티브 TTS를 사용한 음성 안내 Hook입니다.

```tsx
import { useTTS } from '@/hooks/useTTS';

const { supported, ready, speaking, speak, cancel } = useTTS('ko-KR');

// 음성 안내 재생
speak('안내 메시지', {
  rate: 1,      // 속도 (0.1~10)
  pitch: 1.1,   // 음높이 (0~2)
  volume: 1,    // 볼륨 (0~1)
});
```

### useAudioRecorder
오디오 녹음을 관리하는 Hook입니다.

```tsx
import { useAudioRecorder } from '@/hooks/useAudioRecorder';

const { 
  isRecording, 
  audioBlob, 
  audioUrl, 
  startRecording, 
  stopRecording, 
  stream 
} = useAudioRecorder();
```

**반환값:**
- `isRecording`: 녹음 중 여부
- `audioBlob`: 녹음된 오디오 Blob
- `audioUrl`: 오디오 URL (재생용)
- `startRecording`: 녹음 시작 함수
- `stopRecording`: 녹음 중지 함수
- `stream`: MediaStream 객체

## 🎨 UI/UX 특징

### 색상 시스템
각 훈련별로 고유한 색상 테마를 사용합니다:

| 훈련 | 색상 | Tailwind 클래스 |
|------|------|-----------------|
| MPT | 파란색 | `bg-blue-100`, `border-blue-400`, `text-blue-800` |
| 크레셴도 | 노란색 | `bg-yellow-100`, `border-yellow-400`, `text-yellow-800` |
| 데크레셴도 | 보라색 | `bg-purple-100`, `border-purple-400`, `text-purple-800` |
| 순간 강약 | 핑크색 | `bg-pink-100`, `border-pink-400`, `text-pink-800` |
| 연속 강약 | 초록색 | `bg-green-100`, `border-green-400`, `text-green-800` |

### 반응형 디자인
- 모바일: 세로 레이아웃, 축소된 여백
- 태블릿: 적당한 여백, 중간 버튼 크기
- 데스크톱: 넓은 레이아웃, 큰 버튼

### 접근성
- 명확한 버튼 레이블
- 충분한 터치 영역 (최소 44x44px)
- 시각적 피드백 (색상, 애니메이션)
- 음성 안내 제공 (TTS)

## 🔐 권한 및 보안

### 필요한 권한
- **마이크 권한**: 녹음 기능에 필수
  - 첫 녹음 시 브라우저에서 자동으로 요청
  - HTTPS 환경 권장

### 인증
- 모든 발성 연습 페이지는 로그인 필요
- `ProtectedRoute` 컴포넌트로 보호

## 🚀 사용 예시

### 페이지에서 사용

```tsx
import { useNavigate } from 'react-router-dom';

const MyComponent = () => {
  const navigate = useNavigate();

  const handleStartVoiceTraining = () => {
    navigate('/voice-training');
  };

  return (
    <button onClick={handleStartVoiceTraining}>
      발성 연습 시작
    </button>
  );
};
```

### 직접 특정 훈련으로 이동

```tsx
// MPT 훈련 2번째 시도로 이동
navigate('/voice-training/mpt?attempt=2');

// 크레셴도 훈련 시작
navigate('/voice-training/crescendo?attempt=1');
```

## 📝 주요 상태 관리

각 훈련 페이지는 다음 상태를 관리합니다:

```tsx
const [blob, setBlob] = useState<Blob | null>(null);       // 녹음 Blob
const [url, setUrl] = useState<string>('');                // 녹음 URL
const attempt = parseInt(searchParams.get('attempt') || '1', 10); // 시도 횟수
```

## 🎯 향후 확장 가능성

### API 연동
`src/api/voice-training/` 디렉토리에 API 함수들을 추가할 수 있습니다:

```
src/api/voice-training/
├── uploadRecording.ts      # 녹음 업로드
├── getTrainingHistory.ts   # 훈련 이력 조회
└── submitTrainingResult.ts # 훈련 결과 제출
```

### 훈련 데이터 저장
현재는 로컬에서만 녹음을 처리하지만, 향후 서버에 업로드하여 저장할 수 있습니다.

```tsx
// 예시: 녹음 업로드
const handleRecordEnd = async (blob: Blob, url: string) => {
  setBlob(blob);
  setUrl(url);
  
  // 서버에 업로드
  try {
    await uploadRecording(blob, {
      trainingType: 'mpt',
      attempt: attempt,
    });
    toast.success('녹음이 저장되었습니다!');
  } catch (error) {
    toast.error('저장 실패');
  }
};
```

## 🐛 문제 해결

### 마이크 권한 거부됨
```tsx
// useAudioRecorder.ts에서 처리
catch (error) {
  console.error('Error accessing microphone:', error);
  alert('마이크 접근 권한이 필요합니다.');
}
```

### TTS가 작동하지 않음
- Safari에서는 일부 음성이 제한될 수 있습니다
- `supported` 상태를 확인하여 버튼 비활성화 처리

### 오디오 시각화가 보이지 않음
- 녹음 시작 후에만 시각화가 활성화됩니다
- `active={isRecording}` prop 확인

## 📚 참고 자료

- [Web Audio API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API)
- [MediaRecorder API](https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder)
- [Speech Synthesis API](https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesis)
- [Canvas API](https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API)

