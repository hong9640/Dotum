import logging
import functools
import warnings
from typing import Callable, Any
from datetime import datetime

# 불필요한 외부 라이브러리 로그 억제
logging.getLogger('numba').setLevel(logging.WARNING)
logging.getLogger('numba.core').setLevel(logging.WARNING)
logging.getLogger('numba.core.ssa').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('google').setLevel(logging.WARNING)
logging.getLogger('google.auth').setLevel(logging.WARNING)
logging.getLogger('wavlm').setLevel(logging.WARNING)  # WavLM Config 로그 억제

# Torch 경고 억제
warnings.filterwarnings('ignore', category=UserWarning, module='torch')
warnings.filterwarnings('ignore', message='.*stft with return_complex.*')
warnings.filterwarnings('ignore', message='.*weight_norm.*')
warnings.filterwarnings('ignore', category=FutureWarning, module='librosa')


def setup_logger(name: str = "serving-server", level: int = logging.INFO) -> logging.Logger:
    """
    로거 설정 및 반환
    
    Args:
        name: 로거 이름
        level: 로깅 레벨
        
    Returns:
        logging.Logger: 설정된 로거 인스턴스
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # 콘솔 핸들러 설정
        handler = logging.StreamHandler()
        handler.setLevel(level)
        
        # 포맷 설정
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        logger.setLevel(level)
    
    return logger


def log_api_call(func: Callable) -> Callable:
    """
    API 엔드포인트 함수 데코레이터
    요청 시작/종료 및 처리 시간을 자동으로 로깅
    
    Args:
        func: API 엔드포인트 함수
        
    Returns:
        데코레이트된 함수
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        logger = setup_logger(func.__module__)
        
        # 함수 정보 추출
        func_name = func.__name__
        start_time = datetime.now()
        
        # 요청 시작 로깅
        logger.info(f"Starting {func_name}")
        
        try:
            # 요청 파라미터 로깅 (kwargs만)
            if kwargs:
                # 민감한 정보는 마스킹
                safe_kwargs = {}
                for key, value in kwargs.items():
                    if isinstance(value, str) and len(value) > 100:
                        safe_kwargs[key] = value[:50] + "..."
                    else:
                        safe_kwargs[key] = value
                logger.debug(f"{func_name} params: {safe_kwargs}")
            
            # 함수 실행
            result = await func(*args, **kwargs)
            
            # 처리 시간 계산
            process_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # 성공 로깅
            logger.info(f"{func_name} completed successfully in {process_time:.2f}ms")
            
            return result
            
        except Exception as e:
            # 에러 발생 시 처리 시간 계산
            process_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # 에러 로깅
            logger.error(f"{func_name} failed after {process_time:.2f}ms: {str(e)}")
            raise
    
    return wrapper


def log_step(step_name: str, details: str = None):
    """
    워크플로우 단계 로깅 헬퍼 함수
    
    Args:
        step_name: 단계 이름
        details: 추가 상세 정보
    """
    logger = setup_logger()
    
    if details:
        logger.info(f"{step_name}: {details}")
    else:
        logger.info(f"{step_name}")


def log_success(message: str, **kwargs):
    """
    성공 메시지 로깅 헬퍼 함수
    
    Args:
        message: 성공 메시지
        **kwargs: 추가 정보 (키=값 형태로 로깅)
    """
    logger = setup_logger()
    
    if kwargs:
        details = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
        logger.info(f"✓ {message} ({details})")
    else:
        logger.info(f"✓ {message}")


def log_error(message: str, error: Exception = None, **kwargs):
    """
    에러 메시지 로깅 헬퍼 함수
    
    Args:
        message: 에러 메시지
        error: Exception 객체 (선택사항)
        **kwargs: 추가 정보
    """
    logger = setup_logger()
    
    error_details = ""
    if error:
        error_details = f": {str(error)}"
    
    if kwargs:
        details = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
        logger.error(f"✗ {message} ({details}){error_details}")
    else:
        logger.error(f"✗ {message}{error_details}")


def log_warning(message: str, **kwargs):
    """
    경고 메시지 로깅 헬퍼 함수
    
    Args:
        message: 경고 메시지
        **kwargs: 추가 정보
    """
    logger = setup_logger()
    
    if kwargs:
        details = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
        logger.warning(f"⚠ {message} ({details})")
    else:
        logger.warning(f"⚠ {message}")


# 전역 로거 인스턴스
logger = setup_logger()
