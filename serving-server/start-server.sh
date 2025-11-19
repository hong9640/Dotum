#!/bin/bash

# ======================================================================
# Serving Server 시작 스크립트
# ======================================================================
# GCE GPU VM에서 Serving Server를 빠르게 시작합니다.
#
# 사용 방법:
#   chmod +x start-server.sh
#   ./start-server.sh
# ======================================================================

set -e

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "======================================================================="
echo "Serving Server 시작"
echo "======================================================================="

# GPU 확인
echo -e "\n${YELLOW}GPU 확인:${NC}"
nvidia-smi --query-gpu=index,name,memory.total --format=csv,noheader

# 기존 컨테이너 정리
echo -e "\n${YELLOW}기존 컨테이너 정리 중...${NC}"
docker-compose down 2>/dev/null || true

# Docker 이미지 빌드 및 실행
echo -e "\n${YELLOW}Docker 이미지 빌드 및 서비스 시작...${NC}"
docker-compose up -d --build

# 로그 확인
echo -e "\n${YELLOW}서비스 시작 중... (20초 대기)${NC}"
sleep 20

# 헬스 체크
echo -e "\n${YELLOW}헬스 체크:${NC}"
if curl -f http://localhost:8001/health 2>/dev/null; then
    echo -e "${GREEN}✓ 서비스 정상 동작 중!${NC}"
else
    echo -e "${YELLOW}⚠ 서비스 시작 중... 로그를 확인하세요.${NC}"
fi

# 컨테이너 상태
echo -e "\n${YELLOW}컨테이너 상태:${NC}"
docker ps -a | grep serving-server-gpu

echo ""
echo "======================================================================="
echo -e "${GREEN}✓ 서비스 시작 완료${NC}"
echo "======================================================================="
echo ""
echo "다음 명령어로 로그를 확인할 수 있습니다:"
echo "  docker logs -f serving-server-gpu"
echo ""
echo "GPU 사용 확인:"
echo "  watch -n 1 nvidia-smi"
echo ""
echo "서비스 중지:"
echo "  docker-compose down"
echo ""
