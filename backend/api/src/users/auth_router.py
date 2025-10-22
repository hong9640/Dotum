from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.database import get_session
from . import auth_service

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["auth"],
)

@router.post("/signup", )
async def usersignup():
    pass

@router.post("/login", )
async def userlogin():
    pass

@router.post("/logout", )
async def userlogout():
    pass

@router.delete("/leave",)
async def userleave():
    pass