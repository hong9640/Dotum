# GCE GPU VM 배포 가이드

Google Compute Engine GPU 인스턴스에 Serving Server를 배포하는 상세 가이드입니다.

---

## 📋 사전 준비

### 1. GCP 프로젝트 및 권한

- Google Cloud Project (활성화된 결제 계정)
- Compute Engine API 활성화
- GPU 할당량 확인 (기본적으로 T4 GPU는 0개 할당)

### 2. GPU 할당량 요청 (필요시)

```bash
# 현재 할당량 확인
gcloud compute project-info describe --project=YOUR_PROJECT_ID

# GPU 할당량 증가 요청
# https://console.cloud.google.com/iam-admin/quotas
# 검색: "GPUs (all regions)" 또는 "NVIDIA T4 GPUs"
# 할당량 증가 요청 (최소 1개)
```

---

## 🖥️ GPU VM 생성

### 1. 기본 설정

```bash
export PROJECT_ID=your-project-id
export ZONE=asia-northeast3-a  # 서울 리전
export INSTANCE_NAME=serving-server-gpu
export MACHINE_TYPE=n1-standard-4
export GPU_TYPE=nvidia-tesla-t4
export GPU_COUNT=1
```

### 2. VM 인스턴스 생성

```bash
gcloud compute instances create $INSTANCE_NAME \
  --project=$PROJECT_ID \
  --zone=$ZONE \
  --machine-type=$MACHINE_TYPE \
  --accelerator=type=$GPU_TYPE,count=$GPU_COUNT \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=100GB \
  --boot-disk-type=pd-ssd \
  --maintenance-policy=TERMINATE \
  --metadata=install-nvidia-driver=True \
  --tags=serving-server \
  --scopes=https://www.googleapis.com/auth/cloud-platform
```

### 3. SSH 접속

```bash
gcloud compute ssh $INSTANCE_NAME --zone=$ZONE
```

---

## 🔧 환경 설정

### 1. NVIDIA Driver 설치 확인

```bash
# Driver 자동 설치 진행 상황 확인 (5-10분 소요)
sudo journalctl -u google-startup-scripts.service -f

# 설치 완료 후 GPU 확인
nvidia-smi

# 예상 출력:
# +-----------------------------------------------------------------------------+
# | NVIDIA-SMI 525.x.x       Driver Version: 525.x.x       CUDA Version: 12.0  |
# |-------------------------------+----------------------+----------------------+
# | GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
# |   0  Tesla T4            Off  | 00000000:00:04.0 Off |                    0 |
# +-----------------------------------------------------------------------------+
```

### 2. Docker 설치

```bash
# Docker 설치
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 현재 사용자를 docker 그룹에 추가
sudo usermod -aG docker $USER

# 변경사항 적용을 위해 재로그인 또는 다음 명령 실행
newgrp docker

# Docker 설치 확인
docker --version
```

### 3. NVIDIA Container Toolkit 설치

```bash
# Repository 설정
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

# 패키지 설치
sudo apt-get update
sudo apt-get install -y nvidia-docker2

# Docker 재시작
sudo systemctl restart docker

# GPU 테스트
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

---

## 📦 서비스 배포

### 1. 프로젝트 설정

```bash
# 프로젝트 클론 (Git 설치 필요시)
sudo apt-get install -y git
git clone https://github.com/your-org/serving-server.git
cd serving-server

# 또는 rsync로 로컬에서 파일 전송
# rsync -avz -e "gcloud compute ssh --zone=$ZONE" \
#   ./ $INSTANCE_NAME:~/serving-server/
```

### 2. 환경 변수 설정

```bash
# .env 파일 생성
cat > .env << EOF
GCP_PROJECT_ID=$PROJECT_ID
GCS_BUCKET=your-bucket-name
GCS_CREDENTIAL_PATH=credentials/key.json
DEBUG=false
EOF
```

### 3. GCS 인증 설정

```bash
# credentials 디렉토리 생성
mkdir -p credentials

# 방법 1: 로컬에서 키 파일 업로드
# gcloud compute scp /path/to/key.json \
#   $INSTANCE_NAME:~/serving-server/credentials/key.json --zone=$ZONE

# 방법 2: VM의 서비스 계정 사용 (권장)
# VM 생성 시 --scopes 옵션으로 권한 부여했다면 별도 키 불필요
```

### 4. Docker Compose 설치

```bash
# Docker Compose 설치
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 설치 확인
docker-compose --version
```

### 5. 서비스 시작

```bash
# Docker 이미지 빌드 및 실행
docker-compose up -d --build

# 로그 확인
docker logs -f serving-server-gpu

# GPU 사용 확인
nvidia-smi -l 1  # 1초마다 갱신

# 상태 확인
curl http://localhost:8001/health
```

---

## 🌐 외부 접속 설정

### 1. 방화벽 규칙 생성

```bash
# 방화벽 규칙 생성 (8001 포트 오픈)
gcloud compute firewall-rules create allow-serving-server \
  --project=$PROJECT_ID \
  --direction=INGRESS \
  --action=ALLOW \
  --rules=tcp:8001 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=serving-server \
  --description="Allow access to Serving Server on port 8001"
```

### 2. 외부 IP 확인

```bash
# 외부 IP 조회
export EXTERNAL_IP=$(gcloud compute instances describe $INSTANCE_NAME \
  --zone=$ZONE \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

echo "External IP: $EXTERNAL_IP"
```

### 3. 외부에서 테스트

```bash
# Health check
curl http://$EXTERNAL_IP:8001/health

# API 테스트
curl -X POST http://$EXTERNAL_IP:8001/api/v1/lip-video-optimized \
  -H "Content-Type: application/json" \
  -d '{
    "word": "안녕하세요",
    "user_video_gs": "gs://your-bucket/input.mp4",
    "output_video_gs": "gs://your-bucket/output.mp4",
    "tts_lang": "ko"
  }'
```

---

## 📊 모니터링

### 1. GPU 모니터링

```bash
# 실시간 GPU 사용률 확인
nvidia-smi -l 1

# GPU 메트릭 로깅
nvidia-smi dmon -s pucvmet
```

### 2. Docker 로그

```bash
# 실시간 로그
docker logs -f serving-server-gpu

# 최근 100줄
docker logs --tail 100 serving-server-gpu

# 타임스탬프 포함
docker logs -t serving-server-gpu
```

### 3. 리소스 모니터링

```bash
# Docker 컨테이너 리소스 사용률
docker stats serving-server-gpu

# 시스템 리소스
htop  # 설치: sudo apt-get install htop
```

---

## 💰 비용 최적화

### 1. VM 사양별 비용 (서울 리전 기준, 2024년)

| VM 타입          | GPU       | vCPU | 메모리 | 시간당 비용 | 월 예상 비용 |
| ---------------- | --------- | ---- | ------ | ----------- | ------------ |
| n1-standard-4    | T4 x 1    | 4    | 15GB   | ~$0.74      | ~$540        |
| n1-standard-8    | T4 x 1    | 8    | 30GB   | ~$0.94      | ~$685        |
| n1-highmem-4     | T4 x 1    | 4    | 26GB   | ~$0.82      | ~$597        |
| **권장 시작 사양** | **T4 x 1** | **4** | **15GB** | **~$0.74** | **~$540** |

### 2. 비용 절감 방법

#### 선점형(Preemptible) VM 사용

```bash
# 선점형 VM으로 생성 (최대 80% 할인!)
gcloud compute instances create $INSTANCE_NAME \
  --preemptible \
  --maintenance-policy=TERMINATE \
  ... # 기타 옵션 동일
```

**주의사항**:
- 최대 24시간만 실행 가능
- 언제든지 종료될 수 있음
- 프로덕션 환경에는 비권장

#### 사용하지 않을 때 중지

```bash
# VM 중지 (디스크 비용만 발생)
gcloud compute instances stop $INSTANCE_NAME --zone=$ZONE

# VM 시작
gcloud compute instances start $INSTANCE_NAME --zone=$ZONE
```

#### 예약 할인 사용

- 1년/3년 약정 할인 (최대 57% 할인)
- 안정적인 워크로드에 적합

---

## 🔄 유지보수

### 1. 서비스 재시작

```bash
# Docker Compose 재시작
docker-compose restart

# 전체 재빌드
docker-compose down
docker-compose up -d --build
```

### 2. 업데이트

```bash
# 코드 업데이트
cd ~/serving-server
git pull

# 재배포
docker-compose up -d --build
```

### 3. 백업

```bash
# 디스크 스냅샷 생성
gcloud compute disks snapshot $INSTANCE_NAME \
  --zone=$ZONE \
  --snapshot-names=${INSTANCE_NAME}-snapshot-$(date +%Y%m%d)
```

---

## 🐛 문제 해결

### GPU를 인식하지 못하는 경우

```bash
# NVIDIA Driver 재설치
sudo /opt/deeplearning/install-driver.sh

# Docker 재시작
sudo systemctl restart docker

# 재부팅
sudo reboot
```

### OOM (Out of Memory) 오류

```bash
# 메모리 사용량 확인
docker stats

# 더 큰 메모리의 VM으로 변경
gcloud compute instances stop $INSTANCE_NAME --zone=$ZONE
gcloud compute instances set-machine-type $INSTANCE_NAME \
  --zone=$ZONE \
  --machine-type=n1-highmem-4
gcloud compute instances start $INSTANCE_NAME --zone=$ZONE
```

### 포트 접속 불가

```bash
# 방화벽 규칙 확인
gcloud compute firewall-rules list --filter="name=allow-serving-server"

# VM 태그 확인
gcloud compute instances describe $INSTANCE_NAME \
  --zone=$ZONE \
  --format="get(tags.items[])"

# 로컬에서 테스트
curl -v http://$EXTERNAL_IP:8001/health
```

---

## 📚 참고 자료

- [GCE GPU 문서](https://cloud.google.com/compute/docs/gpus)
- [NVIDIA Docker 문서](https://github.com/NVIDIA/nvidia-docker)
- [Docker Compose 문서](https://docs.docker.com/compose/)

---

**작성일**: 2025-11-04  
**버전**: 1.0
