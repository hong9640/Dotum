from fastapi import File, UploadFile
from api.core.config import Settings
from fastapi import APIRouter, Depends, status, Path
from starlette.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from api.core.database import get_session
from fastapi.responses import JSONResponse
from ..models.model import User
from ..schemas.schema import Usercheckinfo, FileUploadResponse
from api.modules.auth.services.service import CredentialsException, get_current_user
from api.modules.auth.schemas.schema import (
    FailResponse, 
    ErrorDetail,
    )
from ..services.service import UserUpdateRequest, update_user_profile
router = APIRouter(
    tags=["user"],
)

# --- API ---

@router.get(
    "/me",
    response_model=Usercheckinfo,
    responses= {401: {"model": FailResponse}},
    status_code=status.HTTP_200_OK

)
async def get_my_information(
    current_user: User = Depends(get_current_user)
):
    try:
        return current_user
        
    except CredentialsException:
        error_response = FailResponse(
            status="FAIL",
            error=ErrorDetail(
                code="UNAUTHORIZED",
                message="유효하지 않은 접근입니다. 다시 로그인해주세요."
            )
        )
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=error_response.model_dump()
        )


@router.patch(
    "/me",
    response_model=Usercheckinfo,
    responses={401: {"model": FailResponse}},
    status_code=status.HTTP_200_OK,
)
async def update_my_profile(
    update_data: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    try:
        updated_user = await update_user_profile(
            user_to_update=current_user,
            update_data=update_data,
            db=db
        )
        return updated_user
        
    except CredentialsException:
        error_response = FailResponse(
            status="FAIL",
            error=ErrorDetail(
                code="UNAUTHORIZED",
                message="인증 정보가 유효하지 않습니다."
            )
        )
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=error_response.model_dump()
        )

