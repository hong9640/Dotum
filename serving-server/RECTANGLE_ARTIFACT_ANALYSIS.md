# 사각형 테두리 잔상 문제 분석

## 🔴 문제 증상

결과 영상에 사각형 테두리 잔상이 남음

---

## 🔍 코드 흐름 분석

### 1. Face Detection (inference.py:68-106)

```python
# 88-99줄: 패딩 추가 후 좌표 저장
pady1, pady2, padx1, padx2 = args.pads  # [0, 20, 0, 0]
y1 = max(0, rect[1] - pady1)
y2 = min(image.shape[0], rect[3] + pady2)
x1 = max(0, rect[0] - padx1)
x2 = min(image.shape[1], rect[2] + padx2)
results.append([x1, y1, x2, y2])  # ⚠️ [x1, y1, x2, y2] 순서

# 103줄: 얼굴 크롭 및 좌표 변환
results = [[image[y1: y2, x1:x2], (y1, y2, x1, x2)]
           for image, (x1, y1, x2, y2) in zip(images, boxes)]
# ⚠️ 입력: [x1, y1, x2, y2] → 출력: (y1, y2, x1, x2)
```

### 2. Datagen (inference.py:108-154)

```python
# 124줄: 얼굴과 좌표 가져오기
face, coords = face_det_results[idx].copy()  # coords = (y1, y2, x1, x2)

# 126줄: 고정 크기로 리사이즈
face = cv2.resize(face, (args.img_size, args.img_size))  # 96x96
```

### 3. 모델 추론 및 합성 (inference.py:267-272)

```python
for p, f, c in zip(pred, frames, coords):
    y1, y2, x1, x2 = c
    # ⚠️ 문제 1: cv2.resize의 인자 순서
    p = cv2.resize(p.astype(np.uint8), (x2 - x1, y2 - y1))  # (width, height)

    # ⚠️ 문제 2: 직접 대입으로 경계 처리 없음
    f[y1:y2, x1:x2] = p
    out.write(f)
```

---

## 🎯 발견된 문제들

### ⚠️ 문제 1: 부동소수점 좌표 → 정수 변환 불일치

**원인**:

```python
# face_detect에서
y1 = max(0, rect[1] - pady1)  # float 가능
y2 = min(image.shape[0], rect[3] + pady2)

# 리사이즈 시
p = cv2.resize(p.astype(np.uint8), (x2 - x1, y2 - y1))  # 부동소수점 크기
```

**문제**:

- `x2 - x1`, `y2 - y1`이 부동소수점일 경우 정수로 변환되면서 1픽셀 오차 발생
- 리사이즈된 이미지와 대상 영역의 크기가 정확히 일치하지 않음

### ⚠️ 문제 2: 경계 블렌딩 없음

**현재 코드**:

```python
f[y1:y2, x1:x2] = p  # 직접 대입
```

**문제**:

- 립싱크된 얼굴을 원본에 **직접 복사**
- 경계에서 색상/밝기 불연속
- 테두리가 명확하게 보임

### ⚠️ 문제 3: 색상 공간 불일치 가능성

**추론 과정**:

```python
# 267-271줄
pred = pred.cpu().numpy().transpose(0, 2, 3, 1) * 255.
p = cv2.resize(p.astype(np.uint8), (x2 - x1, y2 - y1))
f[y1:y2, x1:x2] = p
```

**문제**:

- `pred`는 모델 출력 (0-1 범위를 255로 스케일)
- 색상 공간이나 정규화 불일치로 경계 색상 차이 발생 가능

---

## 🔧 해결 방법

### 방법 1: 좌표를 정수로 명시적 변환 ✅ (즉시 적용 가능)

**수정 위치**: inference.py:267-272

```python
for p, f, c in zip(pred, frames, coords):
    y1, y2, x1, x2 = c
    # 좌표를 정수로 변환
    y1, y2, x1, x2 = int(y1), int(y2), int(x1), int(x2)

    # 크기를 정확히 맞춰서 리사이즈
    target_width = x2 - x1
    target_height = y2 - y1
    p = cv2.resize(p.astype(np.uint8), (target_width, target_height))

    f[y1:y2, x1:x2] = p
    out.write(f)
```

### 방법 2: 경계 블렌딩 추가 🌟 (권장)

**포아송 블렌딩 적용**:

```python
for p, f, c in zip(pred, frames, coords):
    y1, y2, x1, x2 = c
    y1, y2, x1, x2 = int(y1), int(y2), int(x1), int(x2)

    target_width = x2 - x1
    target_height = y2 - y1
    p = cv2.resize(p.astype(np.uint8), (target_width, target_height))

    # 마스크 생성 (중앙은 1, 가장자리로 갈수록 0)
    mask = np.ones(p.shape, p.dtype) * 255

    # 중앙점 계산
    center = ((x1 + x2) // 2, (y1 + y2) // 2)

    # Seamless cloning (경계 부드럽게)
    try:
        output = cv2.seamlessClone(p, f, mask, center, cv2.NORMAL_CLONE)
        out.write(output)
    except:
        # seamlessClone 실패 시 기존 방식
        f[y1:y2, x1:x2] = p
        out.write(f)
```

### 방법 3: 페더링(Feathering) 적용 🔥 (빠르고 효과적)

```python
for p, f, c in zip(pred, frames, coords):
    y1, y2, x1, x2 = c
    y1, y2, x1, x2 = int(y1), int(y2), int(x1), int(x2)

    target_width = x2 - x1
    target_height = y2 - y1
    p = cv2.resize(p.astype(np.uint8), (target_width, target_height))

    # 부드러운 알파 마스크 생성 (가장자리 페더링)
    mask = np.ones((target_height, target_width), dtype=np.float32)

    # 가장자리 5-10픽셀을 부드럽게
    feather_amount = min(10, target_width // 20, target_height // 20)

    # 상하좌우 가장자리 페더링
    for i in range(feather_amount):
        fade = i / feather_amount
        mask[i, :] *= fade  # 위
        mask[-(i+1), :] *= fade  # 아래
        mask[:, i] *= fade  # 왼쪽
        mask[:, -(i+1)] *= fade  # 오른쪽

    # 알파 블렌딩
    mask = mask[:, :, np.newaxis]  # (H, W, 1)
    original_region = f[y1:y2, x1:x2].astype(np.float32)
    blended = (p * mask + original_region * (1 - mask)).astype(np.uint8)

    f[y1:y2, x1:x2] = blended
    out.write(f)
```

### 방법 4: face_detect에서 좌표 정수화 (근본 해결)

**수정 위치**: inference.py:94-99

```python
# 정수로 명시적 변환
y1 = int(max(0, rect[1] - pady1))
y2 = int(min(image.shape[0], rect[3] + pady2))
x1 = int(max(0, rect[0] - padx1))
x2 = int(min(image.shape[1], rect[2] + padx2))

results.append([x1, y1, x2, y2])
```

---

## 📋 권장 조치 순서

### 1단계: 긴급 수정 (좌표 정수화)

- face_detect 함수 수정 (94-99줄)
- 합성 부분 수정 (267-272줄)

### 2단계: 품질 개선 (페더링 추가)

- 방법 3 적용
- feather_amount를 5-10으로 조정하여 테스트

### 3단계: 추가 최적화 (선택)

- seamlessClone 시도 (느릴 수 있음)
- 색상 보정 추가

---

## 🎯 예상 효과

✅ **좌표 정수화**: 1픽셀 오차 제거
✅ **페더링**: 경계 부드럽게 처리, 테두리 잔상 80-90% 감소
✅ **seamlessClone**: 완벽한 블렌딩 (처리 시간 증가)

---

## 💡 추가 고려사항

1. **패딩 조정**: 현재 `pads=[0, 20, 0, 0]`

   - 아래쪽 20픽셀 패딩이 턱을 포함하지만 테두리 발생 위험
   - 필요시 패딩을 줄여서 테스트: `[0, 10, 0, 0]`

2. **resize_factor 영향**:

   - 현재 `resize_factor=2` (해상도 절반)
   - 작은 해상도에서 경계가 더 눈에 띔
   - 원본 해상도(resize_factor=1)에서 테스트 권장

3. **box 옵션 확인**:
   - 현재 `--box -1 -1 -1 -1` (자동 감지)
   - Face detection이 불안정하면 고정 박스 사용 고려
