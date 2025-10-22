from fastapi import APIRouter, Depends, status, Path
from starlette.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from api.core.database import get_session

# model
from api.src.users import user_model

router = APIRouter(
    prefix="/api/v1/email",
    tags=["verification"],
)

# --- API ---

@router.get(
    "/duplicate-check?email={email}",
    response_model=,
    summary=""
)
async def userlogin(db: AsyncSession = Depends(get_session)):
    pass
