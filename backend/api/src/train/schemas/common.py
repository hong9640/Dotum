from pydantic import BaseModel
from typing import List, Optional


class DeleteSuccessResponse(BaseModel):
    message: str = "삭제에 성공했습니다."


class ErrorDetail(BaseModel):
    """에러 상세 정보"""
    field: Optional[str] = None
    message: str


class ErrorResponse(BaseModel):
    """일반 에러 응답"""
    detail: str | List[ErrorDetail]


class NotFoundErrorResponse(BaseModel):
    """404 Not Found 에러 응답"""
    detail: str


class ConflictErrorResponse(BaseModel):
    """409 Conflict 에러 응답"""
    detail: str


class BadRequestErrorResponse(BaseModel):
    """400 Bad Request 에러 응답"""
    detail: str


class UnauthorizedErrorResponse(BaseModel):
    """401 Unauthorized 에러 응답"""
    detail: str = "인증이 필요합니다."

class ProcessingErrorResponse(BaseModel):
    """202 Accepted 에러 응답"""
    detail: str = "요청이 성공적으로 접수되었으나, 처리가 완료되지 않았습니다."
