from fastapi import APIRouter, Response, Depends, status, Cookie, HTTPException
from typing import Annotated
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, EmailStr
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi.responses import JSONResponse
from api.core.database import get_session
from api.modules.user.models.model import User
from ..services.service import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_user, 
    check_email_exists, 
    UsernameAlreadyExistsError,
    InvalidCredentialsError,
    CredentialsException,
    login_user,
    get_current_user,
    soft_delete_user,
    refresh_access_token,
    REFRESH_TOKEN_EXPIRE_DAYS,
    logout_user
    )
from ..schemas.schema import (
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
    TokenRefreshResponse
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
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_session)
):
    user_data_for_service = UserLoginRequest(
        username=form_data.username,
        password=form_data.password
    )
    try:
        login_result = await login_user(user_data=user_data_for_service, db=db)
        response.set_cookie(
            key="refresh_token",
            value=login_result["refresh_token"],
            httponly=True,
            secure=True,  
            samesite="strict",
            expires=datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            path="/"
        )
        return {
            "data": {
                "user": login_result["user"],
                "token": {
                    "access_token": login_result["access_token"],
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
    except Exception as e:
        print(f"로그인 중 예상치 못한 에러 발생: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="로그인 처리 중 오류가 발생했습니다."
        )
    
@router.post(
    "/logout",
    response_model=UserLogoutSuccessResponse,
    status_code=status.HTTP_200_OK
)
async def userlogout(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):

    success = await logout_user(
        refresh_token=refresh_token, 
        user_id=current_user.id, 
        db=db
    )

    response.delete_cookie(key="refresh_token", path="/")

    if success:
        return {"message": "성공적으로 로그아웃되었습니다."}
    else:
        print(f"로그아웃 처리 완료 (User ID: {current_user.id}, DB에 해당 토큰 없음)")
        return {"message": "로그아웃 처리 완료 (토큰 정보 없음)"}

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

@router.post(
    "/token",
    response_model=TokenRefreshResponse,
    summary="액세스 토큰 재발급 (HttpOnly 쿠키, DB 검증, Rotation)"
)
async def refresh_access_token_endpoint(
    response: Response, 
    refresh_token: str | None = Cookie(default=None), 
    db: AsyncSession = Depends(get_session)
):
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found in cookie"
        )

    try:
        new_access_token, new_refresh_token = await refresh_access_token(
            refresh_token, db
        )

        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            secure=True,
            samesite="strict",
            expires=datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            path="/"
        )

        return TokenRefreshResponse(
            access_token=new_access_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    except HTTPException as e:
        response.delete_cookie("refresh_token", path="/")
        raise e
    except Exception as e:
        print(f"Unexpected error during token refresh: {e}")
        response.delete_cookie("refresh_token", path="/") 
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred during token refresh."
        )