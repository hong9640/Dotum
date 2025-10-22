from fastapi import APIRouter, Depends, status, Path
from starlette.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from api.core.database import get_session

# model
from api.src.users import user_model

router = APIRouter(
    prefix="/api/v1/user",
    tags=["user"],
)

# --- API ---

@router.get(
    "/me",
    response_model=,
    summary=""
)
async def userinformation(db: AsyncSession = Depends(get_session)):
    pass

@router.patch(
    "/me",
    response_model=,
    summary=""
)
async def patchprofile(db: AsyncSession = Depends(get_session)):
    pass

@router.post(
    "/files/upload",
    response_model=,
    summary=""
)
async def uploadimage(db: AsyncSession = Depends(get_session)):
    pass