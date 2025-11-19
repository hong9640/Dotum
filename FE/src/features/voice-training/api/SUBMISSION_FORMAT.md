# 🎤 발성 연습 제출 형식

## 📦 백엔드 API 요구사항

### 엔드포인트
```
POST /train/training-sessions/{session_id}/vocal/{item_index}/submit
```

### 요청 형식 (FormData)
```typescript
{
  audio_file: File,      // ✅ 필수 - WAV 형식
  graph_image: File,     // ✅ 필수 - PNG 형식
  graph_video?: File     // ⭕ 선택 - MP4 형식 (현재 미구현)
}
```

---

## 🎯 현재 구현 방식

### 1. 오디오 녹음 (✅ 완료)
**기술:** `MediaRecorder API` + `useAudioRecorder` hook

```typescript
// 녹음 시작
await navigator.mediaDevices.getUserMedia({ audio: true })
const mediaRecorder = new MediaRecorder(stream)

// 녹음 완료 → audioBlob (WAV)
const audioFile = new File([audioBlob], 'mpt_1.wav', { type: 'audio/wav' })
```

**결과물:** `Blob` → WAV 파일

---

### 2. 그래프 시각화 (✅ 완료)
**기술:** `MeydaGraph` 컴포넌트 (Canvas 기반)

**특징:**
- 실시간 RMS → dBFS 변환
- -60 ~ 0 dB 범위 표시
- EMA 스무딩 적용
- 좌→우 스크롤 라인 그래프

```typescript
// 실시간 그리기
analyser.getFloatTimeDomainData(timeDomainData)
const rms = calculateRMS(timeDomainData)
const dBFS = 20 * Math.log10(rms)
ctx.lineTo(x, dbToY(dBFS))
```

---

### 3. 그래프 이미지 캡처 (✅ 완료)
**기술:** `Canvas.toBlob()` API

```typescript
// MeydaGraph에서 이미지 캡처
const captureImage = async (): Promise<Blob | null> => {
  return new Promise((resolve) => {
    canvas.toBlob((blob) => {
      resolve(blob);
    }, 'image/png');
  });
}

// 사용 예시
const graphImageBlob = await graphRef.current?.captureImage();
const graphImageFile = new File([graphImageBlob], 'mpt_1_graph.png', { 
  type: 'image/png' 
});
```

**결과물:** `Blob` → PNG 이미지

---

### 4. 백엔드 전송 (✅ 완료)

```typescript
// src/api/voice-training/index.ts
export const submitVocalItem = async ({
  sessionId,
  itemIndex,
  audioFile,      // WAV 파일
  graphImage,     // PNG 파일
  // graphVideo,  // 미구현 (선택사항)
  onUploadProgress
}: SubmitVocalItemRequest) => {
  const formData = new FormData();
  formData.append('audio_file', audioFile);
  formData.append('graph_image', graphImage);
  
  const response = await apiClient.post(
    `/train/training-sessions/${sessionId}/vocal/${itemIndex}/submit`,
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress
    }
  );
  
  return response.data;
};
```

---

## 📊 데이터 플로우

```
사용자 녹음 시작
    ↓
[1] MediaRecorder → audioBlob (WAV)
    ↓
[2] MeydaGraph 실시간 그래프 그리기 (Canvas)
    ↓
사용자 녹음 종료 → "제출하기" 버튼 클릭
    ↓
[3] canvas.toBlob() → graphImageBlob (PNG)
    ↓
[4] FormData 생성
    - audio_file: audioBlob
    - graph_image: graphImageBlob
    ↓
[5] POST /train/training-sessions/{id}/vocal/{idx}/submit
    ↓
[6] 백엔드 응답
    - session (업데이트된 세션 정보)
    - is_completed 확인
    ↓
[7] is_completed === true → 다음 시도/연습 활성화
```

---

## 🎬 그래프 영상 (미구현, 선택사항)

### 구현 시 필요 기술
```typescript
// MediaRecorder로 Canvas 스트림 녹화
const canvasStream = canvas.captureStream(30); // 30 FPS
const videoRecorder = new MediaRecorder(canvasStream, {
  mimeType: 'video/webm;codecs=vp9',
  videoBitsPerSecond: 2500000
});

// 녹화 완료 → Blob
const videoBlob = new Blob(chunks, { type: 'video/webm' });

// WebM → MP4 변환 필요 (ffmpeg.wasm)
const mp4Blob = await convertToMP4(videoBlob);
```

**미구현 이유:**
- 백엔드에서 선택사항으로 명시
- 이미지만으로도 충분한 정보 제공
- 추가 구현 시간 및 복잡도 고려

---

## ✅ 체크리스트

- [x] 오디오 녹음 (WAV)
- [x] 실시간 그래프 시각화 (dBFS)
- [x] 그래프 이미지 캡처 (PNG)
- [x] FormData 구성
- [x] API 전송
- [x] is_completed 확인
- [ ] 그래프 영상 녹화 (선택사항, 미구현)

---

## 🚀 사용 예시

```typescript
// src/pages/voice-training/mpt.tsx
const handleSubmit = async (audioBlob: Blob, graphImageBlob: Blob) => {
  const itemIndex = attempt - 1; // MPT: 0, 1, 2
  
  const result = await submitVocalItem({
    sessionId,
    itemIndex,
    audioFile: new File([audioBlob], `mpt_${attempt}.wav`, { 
      type: 'audio/wav' 
    }),
    graphImage: new File([graphImageBlob], `mpt_${attempt}_graph.png`, { 
      type: 'image/png' 
    }),
  });
  
  // 완료 여부 확인
  const currentItem = result.session.training_items?.find(
    item => item.item_index === itemIndex
  );
  
  if (currentItem?.is_completed) {
    setIsCompleted(true); // 다음 단계 활성화
  }
};
```

---

## 📝 파일명 규칙

| 연습 타입 | 오디오 파일 | 그래프 이미지 |
|-----------|-------------|---------------|
| MPT | `mpt_1.wav` | `mpt_1_graph.png` |
| Crescendo | `crescendo_1.wav` | `crescendo_1_graph.png` |
| Decrescendo | `decrescendo_1.wav` | `decrescendo_1_graph.png` |
| Loud-Soft | `loud_soft_1.wav` | `loud_soft_1_graph.png` |
| Soft-Loud | `soft_loud_1.wav` | `soft_loud_1_graph.png` |

(숫자는 attempt: 1, 2, 3)

