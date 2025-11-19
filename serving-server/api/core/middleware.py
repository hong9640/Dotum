import time
import traceback
from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from api.core.config import settings


class LoggingMiddleware(BaseHTTPMiddleware):
    """요청/응답 로깅 및 처리시간 측정"""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        client_ip = request.client.host
        method = request.method
        path = request.url.path

        # 요청 시작 로그
        print(f"[{method}] {path} - from {client_ip}")

        try:
            response: Response = await call_next(request)
            process_time = (time.time() - start_time) * 1000
            print(f"[{method}] {path} - {response.status_code} ({process_time:.2f} ms)")
            return response

        except Exception as e:
            traceback.print_exc()
            process_time = (time.time() - start_time) * 1000
            print(f"[ERROR] {method} {path} ({process_time:.2f} ms) → {e}")

            return JSONResponse(
                status_code=500,
                content={
                    "status": "FAIL",
                    "error": {
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": str(e),
                    },
                },
            )


class SecurityHeaderMiddleware(BaseHTTPMiddleware):
    """보안 헤더 추가"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

def register_middlewares(app):
    """FastAPI 인스턴스에 미들웨어 등록"""
    # CORS 미들웨어 - 모든 Origin 허용 (개발/테스트용)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 모든 Origin 허용
        allow_credentials=True,
        allow_methods=["*"],  # 모든 HTTP 메서드 허용
        allow_headers=["*"],   # 모든 헤더 허용
    )
    
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(SecurityHeaderMiddleware)