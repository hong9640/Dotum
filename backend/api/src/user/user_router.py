from fastapi import File, UploadFile
from api.core.config import Settings
from fastapi import APIRouter, Depends, status, Path
from starlette.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from api.core.database import get_session
from fastapi.responses import JSONResponse
from api.src.user.user_model import User
from api.src.user.user_schema import Usercheckinfo
from api.src.auth.auth_service import CredentialsException, get_current_user
from api.src.auth.auth_schema import (
    FailResponse, 
    ErrorDetail,
    )
from api.src.user.user_service import UserUpdateRequest, update_user_profile, upload_file_to_gcs
from api.src.user.user_schema import FileUploadResponse
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


# 업로드 수정 필요
# @router.put(
#     "/files/upload",
#     response_model=FileUploadResponse,
#     status_code=status.HTTP_200_OK,
# )
# async def upload_image(
#     file: UploadFile = File(...),
#     current_user: User = Depends(get_current_user),
#     settings: Settings = Depends(get_settings)
# ):
#     try:
#         file_url = await upload_file_to_gcs(
#             file=file,
#             username=current_user.username,
#             bucket_name=settings.GCS_BUCKET_NAME
#         )
        
#         return {
#             "data": {
#                 "file_url": file_url,
#                 "message": "파일이 성공적으로 업로드되었습니다."
#             }
#         }
#     except Exception as e:
#         error_response = FailResponse(
#             status="FAIL",
#             error=ErrorDetail(code="FILE_UPLOAD_FAILED", message=str(e))
#         )
#         return JSONResponse(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             content=error_response.model_dump()
#         )