from pydantic import BaseModel, EmailStr
from typing import Literal
from api.src.user.user_enum import UserRoleEnum
from typing import Optional
from datetime import datetime

# ---check---

class Usercheckinfo(BaseModel):
    id: int
    username: EmailStr
    name: str
    role: UserRoleEnum
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# ---update profile---
class UserUpdateRequest(BaseModel):
    """사용자 정보 수정을 위한 요청 스키마"""
    password: Optional[str] = None
    name: Optional[str] = None

# ---file upload---

class FileUploadData(BaseModel):
    file_url: str
    message: str

class FileUploadResponse(BaseModel):
    status: str = "SUCCESS"
    data: FileUploadData
