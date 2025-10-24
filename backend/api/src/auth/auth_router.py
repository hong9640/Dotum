from fastapi import APIRouter, Depends, status
from typing import Annotated
from pydantic import BaseModel, EmailStr
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi.responses import JSONResponse
from api.core.database import get_session
from api.src.user.user_model import User
from .auth_service import (
    create_user, 
    check_email_exists, 
    UsernameAlreadyExistsError,
    InvalidCredentialsError,
    CredentialsException,
    login_user,
    get_current_user,
    soft_delete_user,
    add_token_to_blacklist
    )
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
    VerifyEmailResponse,
    ErrorDetail,
    )

router = APIRouter(
    tags=["auth"],
)

@router.post(
        "/signup", 
        response_model=SignupSuccessResponse, 
        responses= {409: {"model": FailResponse}},
        status_code=status.HTTP_201_CREATED
        )
async def usersignup(user_data: SignupRequest, db: AsyncSession = Depends(get_session)):
    try:
        new_user = await create_user(user_data=user_data, db=db)
        
        return {
            "message": "회원가입이 성공적으로 완료되었습니다.",
            "data": {"user": new_user}
        }
    except UsernameAlreadyExistsError:
        error_response = FailResponse(
            status="FAIL",
            error=ErrorDetail(
                code="USERNAME_ALREADY_EXISTS",
                message="이미 등록된 이메일입니다."
            )
        )
        
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=error_response.model_dump()
        )
    
@router.post(
    "/login",
    response_model=LoginSuccessResponse,
    responses={401: {"model": FailResponse}},
    status_code=status.HTTP_200_OK
)
async def userlogin(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_session)
):
    user_data_for_service = UserLoginRequest(
        username=form_data.username,
        password=form_data.password
    )
    try:
        login_result = await login_user(user_data=user_data_for_service, db=db)
        
        return {
            "data": {
                "user": login_result["user"],
                "token": {
                    "access_token": login_result["access_token"],
                    "refresh_token": login_result["refresh_token"],
                    "token_type": "bearer",
                    "expires_in": login_result["expires_in"]
                }
            }
        }
    except InvalidCredentialsError:
        error_response = FailResponse(
            status="FAIL",
            error=ErrorDetail(
                code="INVALID_CREDENTIALS",
                message="이메일 또는 비밀번호가 일치하지 않습니다."
            )
        )
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=error_response.model_dump()
        )
    
@router.post(
    "/logout",
    response_model=UserLogoutSuccessResponse,
    status_code=status.HTTP_200_OK
)
async def userlogout(
    request_body: UserLogoutRequest,
    current_user: User = Depends(get_current_user)
):
    await add_token_to_blacklist(request_body.refresh_token)
    return {"message": "성공적으로 로그아웃되었습니다."}

@router.delete(
    "/leave",
    response_model=SignoutResponse,
    responses={
        401: {"model": FailResponse}
    },
    status_code=status.HTTP_200_OK
)
async def userleave(
    signout_data: SignoutRequest,
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_session)
):
    try:
        deleted_user = await soft_delete_user(
            user=current_user,
            password=signout_data.password,
            db=db
        )
        return {
            "message": "회원 탈퇴가 완료되었습니다.",
            "data": {
                "user_id": deleted_user.id,
                "deleted_at": deleted_user.deleted_at
            }
        }
    except InvalidCredentialsError as e:
        error_response = FailResponse(
            status="FAIL",
            error=ErrorDetail(code="INVALID_CREDENTIALS", message=str(e))
        )
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=error_response.model_dump()
        )
    except CredentialsException:
        error_response = FailResponse(
            status="FAIL",
            error=ErrorDetail(code="UNAUTHORIZED", message="인증 정보가 유효하지 않습니다.")
        )
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=error_response.model_dump()
        )

@router.get("/emails/{email}", response_model=VerifyEmailResponse)
async def check_email_duplicate(
    email: EmailStr, 
    db: AsyncSession = Depends(get_session)
):
    is_duplicate = await check_email_exists(email=email, db=db)
    message_txt = "이미 등록된 이메일입니다." if is_duplicate else "사용 가능한 이메일입니다."

    return {
        "status": "Duplicate" if is_duplicate else "SUCCESS",
        "data": {
            "email": email,
            "is_duplicate": is_duplicate,
            "message": message_txt
        }
    }