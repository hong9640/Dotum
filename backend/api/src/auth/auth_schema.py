from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Literal
from api.src.user.user_enum import UserRoleEnum
from typing import Optional
from datetime import datetime

# ---login---

class UserLoginRequest(BaseModel):
    username: EmailStr
    password: str

class UserInfo(BaseModel):
    user_id: int = Field(validation_alias='id')
    username: EmailStr
    name: str
    role: UserRoleEnum
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class TokenInfo(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class LoginSuccessData(BaseModel):
    user: UserInfo
    token: TokenInfo

class LoginSuccessResponse(BaseModel):
    status: str = "SUCCESS"
    data: LoginSuccessData

# ---Fail Response Schemas ---

class ErrorDetail(BaseModel):
    """실패 응답의 error 객체 스키마"""
    code: str
    message: str

class FailResponse(BaseModel):
    """실패 시 전체 응답 스키마"""
    status: Literal["FAIL"]
    error: ErrorDetail

# ---logout---

class UserLogoutRequest(BaseModel):
    refresh_token: str

class UserLogoutSuccessResponse(BaseModel):
    status: str = "SUCCESS"
    message: str

# ---singup---
class SignupRequest(BaseModel):
    username: EmailStr
    password: str
    name: str

class SignupSuccessUser(BaseModel):
    user_id: int = Field(validation_alias='id')
    username: EmailStr
    name: str
    role: str 
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class SignupSuccessData(BaseModel):
    user: SignupSuccessUser

class SignupSuccessResponse(BaseModel):
    status: str = "SUCCESS"
    data: SignupSuccessData
    message: str

# ---signout---

class SignoutRequest(BaseModel):
    password: str

class SignoutData(BaseModel):
    user_id: int
    deleted_at: Optional[datetime]
    class Config:
        from_attributes = True

class SignoutResponse(BaseModel):
    status: str = "SUCCESS"
    message: str
    data: SignoutData

# ---verify---

class VerifyInfo(BaseModel):
    email: EmailStr
    is_duplicate: bool
    message: str
    class Config:
        from_attributes = True

class VerifyEmailResponse(BaseModel):
    status: str 
    data: VerifyInfo

# ---tocken---
class TokenRefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int