from pydantic import BaseModel, EmailStr
from typing import Literal
from api.src.users.user_enum import UserRoleEnum

# ---login---

class UserLoginRequest(BaseModel):
    """로그인 요청 본문 스키마"""
    username: EmailStr
    password: str

class UserInfo(BaseModel):
    """성공 응답의 user 객체 스키마"""
    id: int
    username: EmailStr
    name: str
    role: UserRoleEnum

class TokenInfo(BaseModel):
    """성공 응답의 token 객체 스키마"""
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int

class LoginSuccessData(BaseModel):
    """성공 응답의 data 객체 스키마"""
    user: UserInfo
    token: TokenInfo

class LoginSuccessResponse(BaseModel):
    """로그인 성공 시 전체 응답 스키마"""
    status: Literal["SUCCESS"]
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
    """로그아웃 요청 데이터"""
    refresh_token: str

class UserLogoutSuccess(BaseModel):
    status: Literal["SUCCESS"]
    message: str

# ---singin---

class SigninRequest(BaseModel):
    username: EmailStr
    password: str
    name: str
    phone_number: str
    gender: str

class SigininUserinfo(BaseModel):
    id: int
    username: EmailStr
    name: str
    role: UserRoleEnum

class Signininfo(BaseModel):
    user: SigininUserinfo

class SigninSuccessData(BaseModel):
    status: Literal["SUCCESS"]
    data: Signininfo
    message: str

# ---signout---

class SignoutRequest(BaseModel):
    password: str

class Signoutdata(BaseModel):
    user_id: int
    deleted_at: Optional[datetime]

class SignoutResponse(BaseModel):
    status: Literal["SUCCESS"]
    message: str
    data: Signoutdata
