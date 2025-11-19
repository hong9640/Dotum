# Voice Training 구조 개선 제안

## 현재 구조

```
features/voice-training/
├── api/
├── components/
├── hooks/
├── crescendo.tsx          # 루트에 페이지 파일들이 위치
├── decrescendo.tsx
├── loud-soft.tsx
├── soft-loud.tsx
├── mpt.tsx
└── index.tsx
```

## 제안: pages 폴더 생성

다른 feature들과 일관성을 맞추기 위해 `pages` 폴더를 생성하고 페이지 파일들을 이동하는 것을 제안합니다.

### 개선 후 구조

```
features/voice-training/
├── api/
├── components/
├── hooks/
├── pages/                 # 새로 생성
│   ├── crescendo.tsx
│   ├── decrescendo.tsx
│   ├── loud-soft.tsx
│   ├── soft-loud.tsx
│   ├── mpt.tsx
│   └── index.tsx
└── types/                 # 필요시 추가
```

## 작업 내용

1. `features/voice-training/pages/` 폴더 생성
2. 페이지 파일들을 `pages/` 폴더로 이동
3. 라우팅 설정 파일(`App.tsx` 또는 라우터 설정)에서 import 경로 업데이트

## 주의사항

- 라우팅 경로는 변경하지 않아도 됩니다 (내부 파일 구조만 변경)
- 각 페이지 파일의 import 경로는 상대 경로로 자동 조정됩니다
- 빌드 후 라우팅이 정상 작동하는지 확인 필요

## 실행 시점

이 작업은 선택사항이며, 현재 구조가 간단하고 잘 작동하고 있으므로 우선순위가 낮습니다.
필요시 별도 작업으로 진행할 수 있습니다.

