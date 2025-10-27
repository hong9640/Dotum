# AI Serving Server

AI 음성/영상 변환 서비스를 제공하는 FastAPI 서버입니다.

## 🚀 주요 기능

- **gTTS TTS 생성**: 텍스트를 음성으로 변환
- **FreeVC 음성 변환**: 음성 변환을 위한 AI 모델
- **Wav2Lip 립싱크**: 립싱크 영상 생성
- **GCS 연동**: Google Cloud Storage를 통한 파일 관리

## 📋 요구사항

- Python 3.11
- Docker & Docker Compose
- GCP 서비스 계정 키 파일

## 🛠️ 설치 및 실행

### 1. 환경 변수 설정

`.env` 파일을 생성하고 다음 내용을 입력하세요:

```bash
GCP_PROJECT_ID=s201-475706
GCS_BUCKET=brain-deck
GCS_CREDENTIAL_PATH=./gcp-key.json
DEBUG=false
```

### 2. GCP 서비스 계정 키 파일 준비

`gcp-key.json` 파일을 `serving-server/` 디렉토리에 배치하세요.

### 3. Docker로 실행

```bash
cd serving-server
docker-compose up -d
```

### 4. 로컬 개발 환경에서 실행

```bash
# 가상환경 생성 및 활성화
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt

# 서버 실행
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

## 📡 API 엔드포인트

### 헬스 체크
```bash
GET http://localhost:8001/health
```

### GCS 연결 테스트
```bash
GET http://localhost:8001/api/v1/gcs/test
```

### 음성/영상 변환
```bash
POST http://localhost:8001/api/v1/lip-video
Content-Type: application/json

{
  "word": "안녕하세요",
  "user_video_gs": "gs://brain-deck/videos/user_video.mp4",
  "output_video_gs": "gs://brain-deck/results/output.mp4",
  "tts_lang": "ko"
}
```

### gTTS를 사용한 음성/영상 변환
```bash
POST http://localhost:8001/api/v1/gtts-lip-video
Content-Type: application/json

{
  "text": "안녕하세요",
  "ref_audio_gs": "gs://brain-deck/audios/reference.wav",
  "face_image_gs": "gs://brain-deck/images/face.jpg",
  "tts_lang": "ko"
}
```

## 📁 프로젝트 구조

```
serving-server/
├── api/
│   ├── core/          # 핵심 설정 및 미들웨어
│   ├── service/       # 비즈니스 로직
│   ├── utils/         # 유틸리티 함수
│   └── main.py        # FastAPI 애플리케이션
├── tests/             # 테스트 파일 (Git에서 무시됨)
├── Dockerfile         # Docker 이미지 빌드 파일
├── docker-compose.yml # Docker Compose 설정
├── requirements.txt   # Python 패키지 의존성
└── README.md          # 이 파일
```

## 🔧 개발 환경 설정

### 포트

- API 서버: `8001` (외부 접근 포트)
- 컨테이너 내부: `8000` (컨테이너 내부 포트)

### 환경 변수

- `GCP_PROJECT_ID`: GCP 프로젝트 ID
- `GCS_BUCKET`: GCS 버킷 이름
- `GCS_CREDENTIAL_PATH`: GCP 서비스 계정 키 파일 경로
- `DEBUG`: 디버그 모드 활성화 여부

## 📝 참고사항

- 테스트 파일은 `tests/` 디렉토리에 있으며 Git에서 무시됩니다.
- GCP 서비스 계정 키 파일은 보안상 Git에 커밋하지 마세요.
- CPU 환경에서 실행되도록 최적화되어 있습니다.

