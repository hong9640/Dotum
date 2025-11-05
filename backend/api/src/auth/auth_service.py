from jose.exceptions import ExpiredSignatureError
import os
import hashlib
import bcrypt
from dotenv import load_dotenv
from datetime import datetime, timedelta
from typing import Annotated
from pydantic import BaseModel, EmailStr
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select,delete
from api.core.database import get_session
from api.src.user.user_enum import UserRoleEnum
from api.src.user.user_model import User
from api.src.token.token_model import RefreshToken
from .auth_schema import (
    UserLoginRequest, 
    SignupRequest,
    )
load_dotenv()

# ---jwt 등 보안 관련 설정---
SECRET_KEY = os.getenv("JWT_SECRET")
if not SECRET_KEY:
    raise ValueError("JWT_SECRET 환경 변수가 설정되지 않았습니다.")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

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

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증 (bcrypt 직접 사용)"""
    try:
        password_bytes = plain_password.encode('utf-8')
        # bcrypt는 72바이트까지만 지원
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        
        # DB에서 가져온 해시가 string이면 bytes로 변환
        if isinstance(hashed_password, str):
            hashed_bytes = hashed_password.encode('utf-8')
        else:
            hashed_bytes = hashed_password
            
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception as e:
        print(f"비밀번호 검증 에러: {e}")
        return False

def hash_password(password: str) -> str:
    """비밀번호 해싱 (bcrypt 직접 사용)"""
    password_bytes = password.encode('utf-8')
    # bcrypt는 72바이트까지만 지원
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
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

    hashed_refresh_token = hash_token(refresh_token)

    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})
        expires_at = datetime.fromtimestamp(payload["exp"])
    except JWTError:
        expires_at = datetime.now() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    new_refresh_token_entry = RefreshToken(
        token_hash=hashed_refresh_token,
        expires_at=expires_at,
        user_id=user.id
    )

    db.add(new_refresh_token_entry)

    try:
        await db.commit()
        await db.refresh(new_refresh_token_entry)
        print(f"새 리프레시 토큰 DB 저장 성공 (User ID: {user.id})")
    except IntegrityError:
        await db.rollback()
        print(f"리프레시 토큰 해시 충돌 발생 (User ID: {user.id})")
    except Exception as e:
        await db.rollback()
        print(f"리프레시 토큰 DB 저장 중 에러: {e}")
        raise HTTPException(status_code=500, detail="Failed to save refresh token.")

    return {
        "user": user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }



async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_session)
) -> User:
    # 토큰이 없는 경우 (oauth2_scheme에서 자동으로 처리되지만 명시적 메시지)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except ExpiredSignatureError:
        # 토큰이 만료된 경우
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        # 기타 JWT 검증 실패 (유효하지 않은 토큰 등)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await get_user_by_email(email=username, db=db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    return user

async def logout_user(
    refresh_token: str, user_id: int, db: AsyncSession
) -> bool:
    if not refresh_token:
        return False

    hashed_token = hash_token(refresh_token)
    stmt = delete(RefreshToken).where(
        RefreshToken.token_hash == hashed_token,
        RefreshToken.user_id == user_id
    )
    result = await db.execute(stmt)
    await db.commit()
    deleted_count = result.rowcount
    
    if deleted_count > 0:
        print(f"로그아웃 성공: 리프레시 토큰 DB에서 삭제 (User ID: {user_id})")
        return True
    else:
        print(f"로그아웃 시도: DB에 해당 리프레시 토큰 없음 (User ID: {user_id})") 
        return False

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

async def refresh_access_token(
    refresh_token: str, db: AsyncSession
) -> tuple[str, str]:

    invalid_token_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    hashed_refresh_token = hash_token(refresh_token)
    stmt = select(RefreshToken).where(RefreshToken.token_hash == hashed_refresh_token)
    result = await db.execute(stmt)
    token_entry = result.scalar_one_or_none()

    if not token_entry:
        print("래프래시 실패: DB에 토큰 값이 없습니다.")
        raise invalid_token_exception
    if token_entry.expires_at < datetime.now():
        print("리프래시 실패: 토큰이 만료되었습니다.") 
        await db.delete(token_entry)
        await db.commit()
        raise invalid_token_exception

    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            print("리프래시 실패: 'sub'가 없습니다.") 
            raise invalid_token_exception
    except JWTError as e:
        print(f"리프래시 실패: Original token JWTError ({e})")
        await db.delete(token_entry)
        await db.commit()
        raise invalid_token_exception

    if token_entry:
        user_id = token_entry.user_id 

        delete_stmt = delete(RefreshToken).where(RefreshToken.id == token_entry.id)
        await db.execute(delete_stmt)

    else:
        raise invalid_token_exception

    new_access_token = create_access_token(data={"sub": username})
    new_refresh_token = create_refresh_token(data={"sub": username})
    hashed_new_refresh = hash_token(new_refresh_token)
    try:
        new_payload = jwt.decode(new_refresh_token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})
        new_expires_at = datetime.fromtimestamp(new_payload["exp"])
    except JWTError:
        new_expires_at = datetime.now() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    new_token_db_entry = RefreshToken(
        token_hash=hashed_new_refresh,
        expires_at=new_expires_at,
        user_id=user_id
    )
    db.add(new_token_db_entry)

    await db.commit()
    print(f"토큰 로테이션 성공: 이전 토큰 삭제, 새 토큰 DB 저장 (User ID: {user_id})")

    return new_access_token, new_refresh_token