from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


class NotFoundException(HTTPException):
    """404 에러"""
    def __init__(self, detail: str = "요청한 리소스를 찾을 수 없습니다"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class AlreadyExistsException(HTTPException):
    """409 에러"""
    def __init__(self, detail: str = "이미 존재하는 리소스입니다"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class UnauthorizedException(HTTPException):
    """401 에러"""
    def __init__(self, detail: str = "인증이 필요합니다"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class ForbiddenException(HTTPException):
    """403 에러"""
    def __init__(self, detail: str = "접근 권한이 없습니다"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class BadRequestException(HTTPException):
    """400 에러"""
    def __init__(self, detail: str = "잘못된 요청입니다"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Pydantic validation 에러를 한글 메시지로 변환"""
    errors = []
    
    for error in exc.errors():
        error_type = error.get("type")
        field = error.get("loc")[-1] if error.get("loc") else "unknown"
        
        # 한글 필드명 매핑
        field_names = {
            "word": "단어",
            "sentence": "문장",
            "name": "이름",
            "word_accuracy": "정확도",
        }
        field_kr = field_names.get(field, field)
        
        # 에러 타입별 한글 메시지
        if error_type == "string_too_short":
            min_length = error.get("ctx", {}).get("min_length", 1)
            message = f"{field_kr}는 최소 {min_length}자 이상이어야 합니다"
        elif error_type == "string_too_long":
            max_length = error.get("ctx", {}).get("max_length", 100)
            message = f"{field_kr}는 최대 {max_length}자 이하여야 합니다"
        elif error_type == "missing":
            message = f"{field_kr}는 필수 항목입니다"
        elif error_type == "value_error":
            # field_validator에서 발생한 커스텀 에러
            message = str(error.get("msg", "")).replace("Value error, ", "")
        elif error_type == "greater_than_equal":
            min_value = error.get("ctx", {}).get("ge", 0)
            message = f"{field_kr}는 {min_value} 이상이어야 합니다"
        elif error_type == "less_than_equal":
            max_value = error.get("ctx", {}).get("le", 1)
            message = f"{field_kr}는 {max_value} 이하여야 합니다"
        elif error_type == "string_type":
            message = f"{field_kr}는 문자열이어야 합니다"
        elif error_type == "int_type":
            message = f"{field_kr}는 정수여야 합니다"
        elif error_type == "float_type":
            message = f"{field_kr}는 숫자여야 합니다"
        else:
            message = error.get("msg", "잘못된 입력입니다")
        
        errors.append({
            "field": field,
            "message": message
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": errors}
    )