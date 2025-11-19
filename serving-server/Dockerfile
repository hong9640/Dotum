# ======================================================================
# Dockerfile for GCE GPU VM Environment
# ======================================================================
# Target: Google Compute Engine GPU Instance (NVIDIA T4/V100/A100)
# Base: CUDA 11.8 + cuDNN 8 (Ubuntu 22.04)
# Python: 3.11
# PyTorch: 2.1.0 (GPU - CUDA 11.8)
# ======================================================================

# ----------------------------------------------------------------------
# Stage 1: builder (빌드 및 패키지 설치 전용 스테이지)
# - uv를 사용하여 모든 AI/ML 라이브러리 설치를 담당합니다.
# - GPU 지원을 위해 NVIDIA CUDA 베이스 이미지 사용
# - 최종 이미지에는 이 스테이지의 설치 결과물만 복사됩니다.
# ----------------------------------------------------------------------
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04 as builder

# 1. Python 3.11 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        software-properties-common \
        wget \
        gnupg \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && \
    apt-get install -y --no-install-recommends \
        python3.11 \
        python3.11-dev \
        python3.11-distutils \
        python3-pip \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Python 3.11을 기본 python으로 설정
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# 2. 시스템 종속성 설치 및 정리: 패키지 컴파일에 필요한 도구 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libfftw3-dev \
        libsndfile1-dev \
        portaudio19-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 3. uv 설치 (공식 이미지에서 복사)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 4. requirements.txt 복사 및 라이브러리 설치 (캐시 최적화 핵심)
WORKDIR /app
COPY requirements.txt .

# PyTorch GPU 버전 먼저 설치 (CUDA 11.8)
RUN uv pip install --system --no-cache-dir \
    torch==2.1.0 \
    torchvision==0.16.0 \
    torchaudio==2.1.0 \
    --index-url https://download.pytorch.org/whl/cu118

# 나머지 패키지 설치
RUN uv pip install --system --no-cache-dir -r requirements.txt

# ----------------------------------------------------------------------
# Stage 2: final (실행 전용 최종 이미지)
# - GPU 지원을 위한 CUDA 런타임 이미지 사용
# - GCE GPU VM 환경에 최적화
# - 꼭 필요한 기본 시스템과 설치된 Python 라이브러리만 포함합니다.
# ----------------------------------------------------------------------
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04 as final

# 1. Python 3.11 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        software-properties-common \
        wget \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && \
    apt-get install -y --no-install-recommends \
        python3.11 \
        python3.11-distutils \
        python3-pip \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Python 3.11을 기본 python으로 설정
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# 2. 필수 런타임 종속성 설치 및 정리
#    - ffmpeg: librosa, audioread, 영상 처리 라이브러리 사용
#    - libsm6, libxext6, libglib2.0-0, libfontconfig1: OpenCV, matplotlib 등 런타임 종속성
#    - curl: healthcheck 용
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        libsm6 \
        libxext6 \
        libglib2.0-0 \
        libfontconfig1 \
        curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 3. 빌드 스테이지에서 설치된 Python 라이브러리 및 실행 파일 복사
COPY --from=builder /usr/local/lib/python3.11/dist-packages /usr/local/lib/python3.11/dist-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 4. 작업 디렉토리 설정 및 파일 복사
WORKDIR /app
COPY models ./models
COPY api ./api
COPY requirements.txt .

# 5. 환경 변수 설정
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # GPU 설정 (GCE GPU VM)
    CUDA_VISIBLE_DEVICES=0 \
    NVIDIA_VISIBLE_DEVICES=all \
    NVIDIA_DRIVER_CAPABILITIES=compute,utility \
    # PyTorch 설정
    TORCH_CUDA_ARCH_LIST="7.0;7.5;8.0;8.6" \
    # 성능 최적화
    OMP_NUM_THREADS=4

# 6. 포트 노출 (GCE 표준 포트)
EXPOSE 8000

# 7. 헬스체크 (선택사항)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# 8. 실행 명령어
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]