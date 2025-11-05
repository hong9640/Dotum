# AI Serving Server - Lip Sync Service (GPU Optimized)

FastAPI 기반 음성/영상 변환 서비스 (FreeVC + Wav2Lip)

## 🚀 성능

- **처리 시간**:
  - GPU 모드: ~12초 (5초 영상 기준) 🚀
  - CPU 모드: ~79초 (5초 영상 기준)
- **최적화**: GPU 가속으로 **92% 성능 향상** ✅
- **API**: RESTful HTTP 엔드포인트
- **배포**: Google Compute Engine GPU VM 지원

## 📊 주요 기능

- **TTS 생성**: gTTS를 사용한 텍스트 → 음성 변환
- **FreeVC GPU**: 음성 스타일 변환 (CUDA 가속, 모델 캐싱 최적화)
- **Wav2Lip GPU**: AI 기반 립싱크 영상 생성 (Static Face Detection 적용)
- **GCS 연동**: Google Cloud Storage 파일 관리
- **GCE GPU VM**: Google Compute Engine GPU 인스턴스 지원

---

## 📋 빠른 시작

### 1. 환경 변수 설정

`.env` 파일 생성:

```bash
GCP_PROJECT_ID=your-project-id
GCS_BUCKET=your-bucket-name
GCS_CREDENTIAL_PATH=credentials/key.json
DEBUG=false
```

### 2. GPU 드라이버 설치 (필수)

```bash
# NVIDIA Docker 설치
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker

# GPU 확인
nvidia-smi
```

### 3. Docker로 실행

```bash
# GPU 모드 (권장)
docker-compose up -d

# CPU 모드 (GPU 없는 경우)
docker-compose -f docker-compose.dev.yml up -d
```

### 4. API 호출

```bash
# Health check
curl http://localhost:8001/health

# GPU 최적화 API 사용 (권장)
curl -X POST http://localhost:8001/api/v1/lip-video-optimized \
  -H "Content-Type: application/json" \
  -d '{
    "word": "안녕하세요",
    "user_video_gs": "gs://bucket/input.mp4",
    "output_video_gs": "gs://bucket/output.mp4",
    "tts_lang": "ko"
  }'
```

---

## 🔥 GCE GPU VM 배포

### 1. GPU VM 인스턴스 생성

```bash
# GCP 프로젝트 설정
export PROJECT_ID=your-project-id
export ZONE=asia-northeast3-a  # 서울 리전
export INSTANCE_NAME=serving-server-gpu

# GPU VM 생성 (NVIDIA T4)
gcloud compute instances create $INSTANCE_NAME \
  --project=$PROJECT_ID \
  --zone=$ZONE \
  --machine-type=n1-standard-4 \
  --accelerator=type=nvidia-tesla-t4,count=1 \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=100GB \
  --boot-disk-type=pd-ssd \
  --maintenance-policy=TERMINATE \
  --metadata=install-nvidia-driver=True

# SSH 접속
gcloud compute ssh $INSTANCE_NAME --zone=$ZONE
```

### 2. VM에서 환경 설정

```bash
# NVIDIA Driver 자동 설치 확인 (약 5-10분 소요)
sudo journalctl -u google-startup-scripts.service -f

# GPU 확인
nvidia-smi

# Docker 설치
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# NVIDIA Docker 설치
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker

# Docker GPU 테스트
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

### 3. 서비스 배포

```bash
# 프로젝트 클론
git clone <your-repo-url>
cd serving-server

# 환경 변수 설정
cat > .env << EOF
GCP_PROJECT_ID=$PROJECT_ID
GCS_BUCKET=your-bucket-name
GCS_CREDENTIAL_PATH=credentials/key.json
EOF

# GCS 인증키 복사
mkdir -p credentials
# 로컬에서 key.json을 credentials/ 폴더에 업로드

# Docker 빌드 및 실행
docker-compose up -d --build

# 로그 확인
docker logs -f serving-server-gpu

# 상태 확인
curl http://localhost:8001/health
```

### 4. 외부 접속 설정 (선택사항)

```bash
# 방화벽 규칙 생성
gcloud compute firewall-rules create allow-serving-server \
  --project=$PROJECT_ID \
  --direction=INGRESS \
  --action=ALLOW \
  --rules=tcp:8001 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=serving-server

# VM에 태그 추가
gcloud compute instances add-tags $INSTANCE_NAME \
  --zone=$ZONE \
  --tags=serving-server

# 외부 IP 확인
gcloud compute instances describe $INSTANCE_NAME \
  --zone=$ZONE \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)'

# 외부에서 접속 테스트
curl http://EXTERNAL_IP:8001/health
```

---

## 📁 프로젝트 구조

```
serving-server/
├── api/
│   ├── core/                      # 설정, 미들웨어, 로거
│   ├── service/
│   │   ├── freevc_optimized.py   # FreeVC 최적화 (NEW)
│   │   ├── ai_service_optimized.py # 최적화 서비스 (NEW)
│   │   └── ai_service.py          # 기존 서비스
│   ├── routes/
│   │   └── optimized.py           # 최적화 엔드포인트 (NEW)
│   └── main.py                    # FastAPI 앱
├── models/
│   ├── FreeVC/                    # FreeVC 모델 및 스크립트
│   └── Wav2Lip/                   # Wav2Lip 모델 및 스크립트
├── Dockerfile                      # 프로덕션 Dockerfile
├── Dockerfile.dev                  # 개발용 Dockerfile
├── docker-compose.yml              # 프로덕션 Docker Compose
├── docker-compose.dev.yml          # 개발용 Docker Compose
├── requirements.txt                # Python 의존성
├── test_optimization.py            # 최적화 테스트 (NEW)
├── SERVING_OPTIMIZATION.md         # 상세 기술 문서 (NEW)
├── OPTIMIZATION_SUMMARY.md         # 최적화 요약 (NEW)
└── README.md                       # 이 파일
```

---

## 📡 API 엔드포인트

### 기본 엔드포인트

| Method | Path      | 설명                            |
| ------ | --------- | ------------------------------- |
| GET    | `/`       | 서버 상태 확인                  |
| GET    | `/health` | 헬스 체크 (모델 파일 존재 여부) |

### 립싱크 API

| Method | Path                          | 설명       | 상태           |
| ------ | ----------------------------- | ---------- | -------------- |
| POST   | `/api/v1/lip-video`           | 기본 API   | ✅ 최적화 적용 |
| POST   | `/api/v1/lip-video-optimized` | 최적화 API | ✅ 테스트용    |

### 유틸리티

| Method | Path                     | 설명           |
| ------ | ------------------------ | -------------- |
| POST   | `/api/v1/preload-models` | 모델 사전 로드 |

---

## 🔧 개발 환경

### 요구사항

- Python 3.11+
- Docker & Docker Compose
- 8GB+ RAM (16GB 권장)
- GCP 서비스 계정 (GCS 접근용)

### 로컬 실행

```bash
# 가상환경
python -m venv .venv
source .venv/bin/activate

# 패키지 설치 (uv 권장)
pip install uv
uv pip install -r requirements.txt

# 서버 실행
uvicorn api.main:app --reload
```

---

## 📊 성능 최적화

### GPU 모드 (v3.0 - 최신)

```
전체: ~12초 (GPU T4 기준, 92% 향상!)
  ├── Download: 0.8s (6.7%)
  ├── Audio+TTS: 0.5s (4.2%)
  ├── FreeVC GPU: 2.0s (16.7%) ← CUDA 가속!
  └── Wav2Lip GPU: 8.7s (72.5%) ← Static Face + GPU!
```

### CPU 모드 (v2.0)

```
전체: 78.81초 (48% 향상)
  ├── Download: 0.83s (1.1%)
  ├── Audio+TTS: 0.47s (0.6%)
  ├── FreeVC: 3.03s (3.8%)
  └── Wav2Lip: 67.17s (85.2%)
```

### 주요 최적화

- ✅ **GPU 가속** (CUDA 11.8 + cuDNN 8)
  - FreeVC: CPU 15s → GPU 2s (87% 개선)
  - Wav2Lip: CPU 136s → GPU 9s (93% 개선)
- ✅ **Static Face Detection** (첫 프레임만 탐지)
  - Face detection: 120s → 5s (96% 개선)
- ✅ **모델 사전 로드** (캐싱)
  - 첫 요청 후 재사용으로 로딩 시간 0초
- ✅ **배치 크기 자동 조정**
  - GPU 메모리에 따라 최적 배치 크기 자동 설정

자세한 내용: [SERVING_OPTIMIZATION.md](./SERVING_OPTIMIZATION.md)

---

## 🧪 테스트

### 자동화 테스트

```bash
# Docker 컨테이너 내부
docker exec serving-server-dev python /app/test_optimization.py

# 예상 출력:
# Model Loading                  ✅ PASS
# Service Integration            ✅ PASS
# 🎉 All tests passed!
```

### API 테스트

```bash
# 모델 사전 로드
curl -X POST http://localhost:8001/api/v1/preload-models

# API 호출
curl -X POST http://localhost:8001/api/v1/lip-video-optimized \
  -H "Content-Type: application/json" \
  -d '{
    "word": "테스트",
    "user_video_gs": "gs://bucket/input.mp4",
    "output_video_gs": "gs://bucket/output.mp4",
    "tts_lang": "ko"
  }'
```

---

## 🔧 Docker 설정

### 개발 환경

```bash
# 빌드 및 실행
docker-compose -f docker-compose.dev.yml up -d

# 로그 확인
docker logs serving-server-dev -f

# 컨테이너 접속
docker exec -it serving-server-dev bash
```

### 프로덕션 환경

```bash
# 빌드 및 실행
docker-compose up -d --build

# 스케일링
docker-compose up -d --scale serving-server=3
```

---

## 📚 문서

- **[OPTIMIZATION_SUMMARY.md](./OPTIMIZATION_SUMMARY.md)** - 최적화 완료 리포트 ⭐
- **[SERVING_OPTIMIZATION.md](./SERVING_OPTIMIZATION.md)** - 상세 기술 문서
- **[test_optimization.py](./test_optimization.py)** - 테스트 스크립트

---

## 🎯 향후 최적화 가능성

1. **모델 양자화** (목표: 12s → 8s)

   - INT8/FP16 양자화
   - TensorRT 최적화
   - 예상 개선: 30-40%

2. **병렬 처리 강화**
   - 멀티 GPU 지원
   - 배치 처리 최적화

자세한 내용: [OPTIMIZATION_SUMMARY.md](./OPTIMIZATION_SUMMARY.md)

---

## 🐛 문제 해결

### Wav2Lip 모델 파일 없음

```bash
cd models/Wav2Lip/checkpoints
wget "https://github.com/Rudrabha/Wav2Lip/releases/download/models/wav2lip_gan.pth" -O Wav2Lip_gan.pth
```

### 메모리 부족 (OOM)

```yaml
# docker-compose.yml
deploy:
  resources:
    limits:
      memory: 12G # 8G → 12G
```

### numba/torch 경고 로그

```
✅ 이미 억제 처리됨 (api/core/logger.py)
```

---

## 📞 기술 지원

- **문서**: `SERVING_OPTIMIZATION.md`, `OPTIMIZATION_SUMMARY.md`
- **테스트**: `test_optimization.py`
- **이슈**: 프로젝트 이슈 트래커

---

## 📄 라이선스

- FreeVC: MIT License
- Wav2Lip: 원본 라이선스 참조

---

**Last Updated**: 2025-11-04  
**Version**: v3.0 (GPU Optimized)  
**Status**: ✅ GPU Production Ready | GCE Compatible
