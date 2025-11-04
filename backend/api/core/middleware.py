import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from api.core.logging import get_logger

logger = get_logger(__name__)

#얼마나 시간이 걸리는지 로깅하는 미들웨어
#DEBUG 모드에서만 사용
class LoggingMiddleware(BaseHTTPMiddleware):
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = (time.time() - start_time) * 1000
        
        if response.status_code < 400:
            logger.info(f"✅ 요청 완료: {request.method} {request.url.path} | "
                       f"상태: {response.status_code} | 시간: {process_time:.1f}ms")
        elif response.status_code < 500:
            logger.warning(f"⚠️  클라이언트 오류: {request.method} {request.url.path} | "
                          f"상태: {response.status_code} | 시간: {process_time:.1f}ms")
        else:
            logger.error(f"❌ 서버 오류: {request.method} {request.url.path} | "
                        f"상태: {response.status_code} | 시간: {process_time:.1f}ms")
        
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
        
        return response

