FROM python:3.11-slim

# 컨테이너 내 작업 디렉토리 설정
WORKDIR /code

# uv 설치
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 의존성 파일만 먼저 복사하여 Docker 빌드 캐시 활용
COPY requirements.txt .

# uv로 의존성 설치
RUN uv pip install --system --no-cache -r requirements.txt

# 소스 코드 복사
COPY . .

# FastAPI 앱이 실행될 8000번 포트 노출
EXPOSE 8000

# 애플리케이션 실행
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]