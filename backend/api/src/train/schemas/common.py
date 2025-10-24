from pydantic import BaseModel


class DeleteSuccessResponse(BaseModel):
    message: str = "삭제에 성공했습니다."
