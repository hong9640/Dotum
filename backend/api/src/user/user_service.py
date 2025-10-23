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
from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from sqlalchemy.orm import selectinload
from api.core.database import get_session
from api.src.user.user_enum import UserRoleEnum
from api.src.user.user_model import User
from api.src.user.user_schema import UserUpdateRequest
from api.src.auth.auth_service import hash_password
KST = timezone(timedelta(hours=9))

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
    user_to_update.updated_at = datetime.now(KST)
    
    db.add(user_to_update)
    await db.commit()
    await db.refresh(user_to_update)
    
    return user_to_update

async def upload_file_to_gcs(
    file: UploadFile,
    username: str,
    bucket_name: str
) -> str:
    
    """파일을 GCS에 업로드하고 public URL을 반환하는 서비스"""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    destination_blob_name = f"images/{username}/{file.filename}"
    blob = bucket.blob(destination_blob_name)
    contents = await file.read()
    await asyncio.to_thread(
        blob.upload_from_string,
        contents,
        content_type=file.content_type
    )
    return blob.public_url
