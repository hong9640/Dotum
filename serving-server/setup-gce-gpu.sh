#!/bin/bash

# ======================================================================
# GCE GPU VM 환경 설정 스크립트
# ======================================================================
# 이 스크립트는 GCE GPU VM에서 Serving Server를 실행하기 위한
# 모든 환경을 자동으로 설정합니다.
#
# 사용 방법:
#   chmod +x setup-gce-gpu.sh
#   ./setup-gce-gpu.sh
# ======================================================================

set -e  # 에러 발생 시 즉시 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "======================================================================="
echo "GCE GPU VM 환경 설정 시작"
echo "======================================================================="

# 1. GPU 드라이버 확인
echo -e "\n${YELLOW}[1/7] GPU 드라이버 확인 중...${NC}"
if command -v nvidia-smi &> /dev/null; then
    echo -e "${GREEN}✓ NVIDIA Driver 설치됨${NC}"
    nvidia-smi --query-gpu=gpu_name,driver_version --format=csv,noheader
else
    echo -e "${RED}✗ NVIDIA Driver가 설치되지 않았습니다.${NC}"
    echo "GCE VM 생성 시 --metadata=install-nvidia-driver=True 옵션을 사용하세요."
    exit 1
fi

# 2. Docker 설치
echo -e "\n${YELLOW}[2/7] Docker 설치 중...${NC}"
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓ Docker 이미 설치됨${NC}"
    docker --version
else
    echo "Docker 설치 중..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo -e "${GREEN}✓ Docker 설치 완료${NC}"
fi

# 3. NVIDIA Container Toolkit 설치
echo -e "\n${YELLOW}[3/7] NVIDIA Container Toolkit 설치 중...${NC}"
if docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi &> /dev/null 2>&1; then
    echo -e "${GREEN}✓ NVIDIA Container Toolkit 이미 설치됨${NC}"
else
    echo "NVIDIA Container Toolkit 설치 중..."
    distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
    curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
    curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
      sudo tee /etc/apt/sources.list.d/nvidia-docker.list

    sudo apt-get update
    sudo apt-get install -y nvidia-docker2
    sudo systemctl restart docker
    echo -e "${GREEN}✓ NVIDIA Container Toolkit 설치 완료${NC}"
fi

# 4. Docker Compose 설치
echo -e "\n${YELLOW}[4/7] Docker Compose 설치 중...${NC}"
if command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}✓ Docker Compose 이미 설치됨${NC}"
    docker-compose --version
else
    echo "Docker Compose 설치 중..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
      -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}✓ Docker Compose 설치 완료${NC}"
fi

# 5. 환경 변수 파일 확인
echo -e "\n${YELLOW}[5/7] 환경 변수 확인 중...${NC}"
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠ .env 파일이 없습니다. 생성합니다...${NC}"
    cat > .env << EOF
GCP_PROJECT_ID=your-project-id
GCS_BUCKET=your-bucket-name
GCS_CREDENTIAL_PATH=credentials/key.json
DEBUG=false
EOF
    echo -e "${YELLOW}⚠ .env 파일을 수정하여 올바른 값을 입력하세요!${NC}"
else
    echo -e "${GREEN}✓ .env 파일 존재${NC}"
fi

# 6. Credentials 디렉토리 확인
echo -e "\n${YELLOW}[6/7] GCS 인증 확인 중...${NC}"
mkdir -p credentials
if [ -f credentials/key.json ]; then
    echo -e "${GREEN}✓ GCS 인증키 존재${NC}"
else
    echo -e "${YELLOW}⚠ credentials/key.json 파일을 배치하세요!${NC}"
fi

# 7. GPU 테스트
echo -e "\n${YELLOW}[7/7] GPU Docker 테스트 중...${NC}"
if docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi; then
    echo -e "${GREEN}✓ GPU Docker 테스트 성공!${NC}"
else
    echo -e "${RED}✗ GPU Docker 테스트 실패${NC}"
    exit 1
fi

# 완료
echo ""
echo "======================================================================="
echo -e "${GREEN}✓ 환경 설정 완료!${NC}"
echo "======================================================================="
echo ""
echo "다음 단계:"
echo "  1. .env 파일 수정 (GCP_PROJECT_ID, GCS_BUCKET 등)"
echo "  2. credentials/key.json 배치"
echo "  3. docker-compose up -d --build"
echo ""
echo "실행 명령어:"
echo "  docker-compose up -d --build        # 서비스 시작"
echo "  docker logs -f serving-server-gpu   # 로그 확인"
echo "  curl http://localhost:8001/health   # 상태 확인"
echo ""
