# AI 서빙 서버 구축 체크리스트

## 프로젝트 개요
- **목표**: GCS SDK 연동 및 AI 서빙 서버 구축
- **주요 기능**: 음성/영상 변환 (TTS → FreeVC → Wav2Lip)
- **환경**: Python 3.11 slim, GCP 서비스 계정 연동

## ✅ 완료된 작업

### 1. 프로젝트 구조 설정
- [x] FastAPI 기반 서버 구조 생성
- [x] Pydantic DTO 모델 정의 (`api/service/dto.py`)
- [x] 설정 관리 시스템 구현 (`api/core/config.py`)
- [x] 미들웨어 설정 (`api/core/middleware.py`)

### 2. 의존성 패키지 관리
- [x] `requirements.txt` 생성 및 패키지 정의
- [x] FastAPI 및 핵심 의존성 추가
- [x] GCP SDK 패키지 추가 (google-cloud-storage, google-cloud-speech, google-cloud-texttospeech)
- [x] PyTorch CUDA 12.1 패키지 추가
- [x] 과학 스택 패키지 추가 (numpy, scipy, librosa, opencv-python 등)
- [x] AI 모델 관련 패키지 추가 (torchcrepe, pyworld, webrtcvad 등)

### 3. GCS SDK 연동
- [x] GCS 클라이언트 래퍼 클래스 구현 (`api/utils/gcs_client.py`)
- [x] 파일 업로드/다운로드 기능 구현
- [x] 파일 존재 여부 확인 기능 구현
- [x] 버킷 파일 목록 조회 기능 구현
- [x] 모델 파일 경로 관리 기능 구현

### 4. AI 서비스 로직 구현
- [x] AI 서비스 클래스 구현 (`api/service/ai_service.py`)
- [x] TTS 오디오 생성 기능 (Google Cloud Text-to-Speech 연동)
- [x] FreeVC 음성 변환 기능 (subprocess 실행)
- [x] Wav2Lip 립싱크 기능 (subprocess 실행)
- [x] 임시 파일 관리 및 정리 로직

### 5. API 엔드포인트 구현
- [x] 헬스 체크 엔드포인트 (`/health`)
- [x] 음성/영상 변환 API (`/api/v1/lip-video`)
- [x] GCS 연결 테스트 API (`/api/v1/gcs/test`)
- [x] 에러 처리 및 로깅 구현

### 6. 환경 설정
- [x] 환경 변수 설정 파일 생성 (`env.example`)
- [x] GCP 프로젝트 설정 (프로젝트 ID: s201-475706, 버킷: brain-deck)
- [x] 서비스 계정 키 파일 경로 설정 (`/etc/gcp/key.json`)

### 7. 테스트 도구
- [x] GCS 연결 테스트 스크립트 생성 (`test_gcs.py`)
- [x] 업로드/다운로드 테스트 기능
- [x] 모델 파일 존재 확인 기능

## 🔄 진행 중인 작업

### 8. GCS 연결 테스트
- [ ] 환경 변수 설정 및 GCS 연결 확인
- [ ] 버킷 접근 권한 테스트
- [ ] 모델 파일 존재 여부 확인

## 📋 남은 작업

### 9. 버킷 조회 및 모델 접근 테스트
- [ ] 버킷 내 파일 목록 조회 테스트
- [ ] 모델 폴더 접근 테스트
- [ ] 생성물을 버킷에 저장하는 테스트

### 10. 실제 워크플로우 테스트
- [ ] TTS 생성 테스트
- [ ] FreeVC 추론 실행 테스트
- [ ] Wav2Lip 추론 실행 테스트
- [ ] 전체 파이프라인 통합 테스트

### 11. 서버 배포 준비
- [ ] Dockerfile 최적화
- [ ] 환경 변수 설정 검증
- [ ] 로깅 시스템 완성
- [ ] 에러 처리 개선

## 🔧 기술 스택

### 백엔드
- **FastAPI**: 웹 API 프레임워크
- **Pydantic**: 데이터 검증 및 직렬화
- **Uvicorn**: ASGI 서버

### AI/ML
- **PyTorch**: 딥러닝 프레임워크 (CUDA 12.1)
- **FreeVC**: 음성 변환 모델
- **Wav2Lip**: 립싱크 모델
- **Google Cloud TTS**: 텍스트 음성 변환

### 클라우드
- **Google Cloud Storage**: 파일 저장소
- **Google Cloud Speech**: 음성 인식
- **Google Cloud Text-to-Speech**: 음성 합성

### 오디오/영상 처리
- **librosa**: 오디오 분석
- **OpenCV**: 영상 처리
- **soundfile**: 오디오 파일 처리

## 📁 프로젝트 구조

```
serving-server/
├── api/
│   ├── core/
│   │   ├── config.py          # 설정 관리
│   │   ├── middleware.py      # 미들웨어
│   │   └── exception.py       # 예외 처리
│   ├── service/
│   │   ├── dto.py            # 데이터 모델
│   │   └── ai_service.py     # AI 서비스 로직
│   ├── utils/
│   │   └── gcs_client.py     # GCS 클라이언트
│   └── main.py               # 메인 애플리케이션
├── requirements.txt          # 의존성 패키지
├── env.example              # 환경 변수 예시
├── test_gcs.py              # GCS 테스트 스크립트
└── CHECKLIST.md             # 이 파일
```

## 🚀 다음 단계

1. **환경 변수 설정**: 실제 GCP 프로젝트 정보로 환경 변수 설정
2. **GCS 연결 테스트**: `test_gcs.py` 실행하여 연결 확인
3. **모델 파일 확인**: 버킷에 필요한 모델 파일들이 존재하는지 확인
4. **API 테스트**: 실제 요청으로 전체 워크플로우 테스트
5. **성능 최적화**: 처리 시간 및 리소스 사용량 최적화

## 📝 참고사항

- 서비스 계정 키 파일 경로: `/etc/gcp/key.json`
- GCP 프로젝트 ID: `s201-475706`
- GCS 버킷명: `brain-deck`
- Python 버전: 3.11 slim (Docker 환경)
- CUDA 버전: 12.1 (PyTorch 호환)
