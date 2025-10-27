# ----------------------------------------------------------------------
# Stage 1: builder (빌드 및 패키지 설치 전용 스테이지)
# - uv 설치 및 모든 AI/ML 라이브러리 설치를 담당합니다.
# - 최종 이미지에는 이 스테이지의 설치 결과물만 복사됩니다.
# ----------------------------------------------------------------------
  FROM python:3.11-slim as builder

  # 1. 시스템 종속성 설치 및 정리: 패키지 컴파일에 필요한 도구 설치
  #    - build-essential, ffmpeg, curl 등
  RUN apt-get update && \
      apt-get install -y --no-install-recommends \
          build-essential \
          ffmpeg \
          curl \
          # PyTorch, SciPy, Numba, OpenCV 등 컴파일에 필요한 추가 라이브러리
          libsm6 \
          libxext6 \
          libglib2.0-0 \
          libfontconfig1 \
      && apt-get clean && rm -rf /var/lib/apt/lists/*
  
  # 2. uv 설치
  #    - 빠른 패키지 설치를 위해 그대로 유지
  RUN pip install uv
  
  # 3. requirements.txt 복사 및 라이브러리 설치 (캐시 최적화 핵심)
  #    - requirements.txt가 변경되지 않는 한, 이 레이어는 캐시를 사용합니다.
  WORKDIR /app
  COPY requirements.txt .
  # --system 플래그 사용 시 uv는 시스템 환경에 설치 (Stage 2로 복사 용이)
  RUN uv pip install --system --no-cache-dir -r requirements.txt
  
  # ----------------------------------------------------------------------
  # Stage 2: final (실행 전용 최종 이미지)
  # - 꼭 필요한 기본 시스템과 설치된 Python 라이브러리만 포함합니다.
  # ----------------------------------------------------------------------
  FROM python:3.11-slim as final
  
  # 1. 필수 시스템 종속성 설치 및 정리 (runtime 전용)
  #    - ffmpeg: librosa, audioread, 영상 처리 라이브러리 사용을 위한 런타임 종속성
  RUN apt-get update && \
      apt-get install -y --no-install-recommends \
          ffmpeg \
          libsm6 \
          libxext6 \
          libglib2.0-0 \
          libfontconfig1 \
      && apt-get clean && rm -rf /var/lib/apt/lists/*
  
  # 2. 빌드 스테이지에서 설치된 Python 라이브러리 및 실행 파일 복사
  #    - /usr/local/lib/python3.11/site-packages: Python 패키지
  #    - /usr/local/bin: 실행 파일 (uvicorn 등)
  COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
  COPY --from=builder /usr/local/bin /usr/local/bin
  WORKDIR /app
  
  # 3. 소스 코드 복사
  COPY . .
  
  # 4. 서비스 계정 키 디렉토리 생성 및 환경 변수 설정 (원본 유지)
  RUN mkdir -p /etc/gcp
  ENV PYTHONUNBUFFERED=1 \
      PYTHONDONTWRITEBYTECODE=1 \
      GCS_CREDENTIAL_PATH=/etc/gcp/key.json
  
  # 5. 포트 노출 및 실행 명령어 (원본 유지)
  EXPOSE 8000
  CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]