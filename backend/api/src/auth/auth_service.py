import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Union
from pydantic import BaseModel, EmailStr
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from sqlalchemy.orm import selectinload
from api.src.user.user_enum import UserRoleEnum
from api.src.user.user_model import User
from .auth_schema import (
    UserLoginRequest, 
    LoginSuccessResponse, 
    FailResponse, 
    UserLogoutRequest,
    UserLogoutSuccessResponse,
    SignupRequest,
    SignupSuccessResponse,
    SignoutRequest,
    SignoutResponse,
    VerifyEmailResponse
    )


SECRET_KEY = os.getenv("JWT_SECRET")
if not SECRET_KEY:
    raise ValueError("JWT_SECRET 환경 변수가 설정되지 않았습니다.")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login", auto_error=True)

def hash_password(password: str) -> str:
    """비밀번호를 해싱"""
    return pwd_context.hash(password)

async def check_email_exists(email: EmailStr, db: AsyncSession) -> bool:
    """DB에서 이메일을 확인하고 존재 여부를 boolean으로 반환"""
    
    stmt = select(User).where(User.username == email)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()
    
    return existing_user is not None

async def create_user(user_data: SignupRequest, db: AsyncSession) -> User:
    """새로운 사용자를 생성하는 서비스 로직"""
    
    # 1. 사용자 중복 확인
    is_duplicate = await check_email_exists(email=user_data.username, db=db)

    if is_duplicate:
        return VerifyEmailResponse()

    # 2. 비밀번호 해싱
    hashed_password = hash_password(user_data.password)

    # 3. DB에 저장할 User 모델 객체 생성
    new_user = User(
        username=user_data.username,
        password=hashed_password,
        name=user_data.name,
        phone_number=user_data.phone_number,
        gender=user_data.gender,
        role=UserRoleEnum.USER
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user

