import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from typing import Annotated
from pydantic import BaseModel, EmailStr
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from sqlalchemy.orm import selectinload
from api.core.database import get_session
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
from api.core.exception import AlreadyExistsException
load_dotenv()

# ---jwt 등 보안 관련 설정---
SECRET_KEY = os.getenv("JWT_SECRET")
if not SECRET_KEY:
    raise ValueError("JWT_SECRET 환경 변수가 설정되지 않았습니다.")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
BLACKLIST = set()

# ---커스텀 예외 클래스---

class CredentialsException(Exception):
    """토큰 자격 증명 실패 시 발생하는 예외"""
    pass

class UsernameAlreadyExistsError(Exception):
    """사용자 이름(이메일)이 이미 존재할 때 발생하는 커스텀 예외"""
    pass
class InvalidCredentialsError(Exception):
    """자격 증명(아이디 또는 비밀번호)이 유효하지 않을 때 발생하는 예외"""
    pass

# ---비밀번호, 토큰 관련 함수---
KST = timezone(timedelta(hours=9))

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(KST) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(KST) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# ---서비스 로직---

async def check_email_exists(email: EmailStr, db: AsyncSession) -> bool:
    """DB에서 이메일을 확인하고 존재 여부를 boolean으로 반환"""
    
    stmt = select(User).where(User.username == email)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()
    
    return existing_user is not None

async def create_user(user_data: SignupRequest, db: AsyncSession) -> User:
    """새로운 사용자를 생성하는 서비스 로직"""
    is_duplicate = await check_email_exists(email=user_data.username, db=db)

    if is_duplicate:
        raise UsernameAlreadyExistsError()

    hashed_password = hash_password(user_data.password)

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

async def get_user_by_email(email: EmailStr, db: AsyncSession) -> User:
    """이메일로 사용자를 조회"""
    stmt = select(User).where(User.username == email)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def login_user(user_data: UserLoginRequest, db: AsyncSession) -> dict:
    user = await get_user_by_email(email=user_data.username, db=db)

    if not user or not verify_password(user_data.password, user.password):
        raise InvalidCredentialsError()

    token_data = {"sub": user.username}
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)
    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception as e:
        print(f"    - 생성 직후 디코딩 실패: {e}")

    return {
        "user": user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

async def add_token_to_blacklist(token: str) -> None:
    """토큰을 블랙리스트에 추가합니다."""
    BLACKLIST.add(token)

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_session)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        print(username)
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await get_user_by_email(email=username, db=db)
    print(user)
    if user is None:
        raise credentials_exception
        
    return user

async def soft_delete_user(user: User, password: str, db: AsyncSession):
    """사용자 소프트 딜리트 서비스"""
    
    # 1. 현재 비밀번호를 다시 한번 확인합니다.
    if not verify_password(password, user.password):
        raise InvalidCredentialsError("비밀번호가 일치하지 않습니다.")
    
    # 2. deleted_at 필드에 현재 시간을 기록합니다.
    user.deleted_at = datetime.now()
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user