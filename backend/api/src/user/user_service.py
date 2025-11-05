import asyncio
from fastapi import UploadFile
from google.cloud import storage
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Union
from pydantic import BaseModel, EmailStr
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from sqlalchemy.orm import selectinload
from api.core.database import get_session
from api.src.user.user_enum import UserRoleEnum
from api.src.user.user_model import User
from api.src.user.user_schema import UserUpdateRequest
from api.src.auth.auth_service import hash_password

async def update_user_profile(
    user_to_update: User, 
    update_data: UserUpdateRequest, 
    db: AsyncSession
) -> User:
    """사용자 프로필 정보 업데이트 서비스"""
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        if field == "password":
            hashed_password = hash_password(value)
            setattr(user_to_update, field, hashed_password)
        else:
            setattr(user_to_update, field, value)
    user_to_update.updated_at = datetime.now()
    
    db.add(user_to_update)
    await db.commit()
    await db.refresh(user_to_update)
    
    return user_to_update
