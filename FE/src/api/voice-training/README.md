# Voice Training API

발성 훈련 API 연동 가이드입니다.

## 📋 Item Index 계산

15개 아이템 (5가지 훈련 × 3회):

| 훈련 타입 | Attempt 1 | Attempt 2 | Attempt 3 | 계산 공식 |
|-----------|-----------|-----------|-----------|-----------|
| MPT | 0 | 1 | 2 | `attempt - 1` |
| Crescendo | 3 | 4 | 5 | `attempt + 2` |
| Decrescendo | 6 | 7 | 8 | `attempt + 5` |
| Loud-Soft | 9 | 10 | 11 | `attempt + 8` |
| Soft-Loud | 12 | 13 | 14 | `attempt + 11` |

## 🔄 플로우

```typescript
// 1. 세션 생성 (첫 훈련 시작 시)
const session = await createVocalSession({
  session_name: '발성 연습',
  type: 'vocal',
  item_count: 15,
  session_metadata: {
    training_types: ['MPT', 'crescendo', 'decrescendo', 'loud_soft', 'soft_loud']
  }
});

// 2. 각 훈련 제출
const result = await submitVocalItem({
  sessionId: session.id,
  itemIndex: calculateItemIndex(trainingType, attempt),
  audioFile: new File([audioBlob], 'audio.wav'),
  graphImage: new File([imageBlob], 'graph.png'),
  graphVideo: graphVideoFile // optional
});

// 3. 완료 확인
const item = result.session.training_items.find(
  item => item.item_index === itemIndex
);
if (item?.is_completed) {
  // 다음 훈련으로 이동 가능
}

// 4. 모든 훈련 완료 후
if (result.session.completed_items === 15) {
  await completeVocalSession(sessionId);
}
```

## 📝 참고사항

- 오디오 파일은 WAV 형식 필수
- 그래프 이미지는 PNG/JPG 형식
- 각 파일 최대 크기: 100MB
- 제출 완료 후 `is_completed` 확인 필수
- 세션 ID는 URL 파라미터로 전달

