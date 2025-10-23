from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi.responses import JSONResponse
from api.core.database import get_session
from api.src.user.user_model import User
from .auth_service import create_user, check_email_exists
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
    VerifyEmailResponse
    )

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["auth"],
)

@router.post(
        "/signup", 
        response_model=SignupSuccessResponse, 
        responses= {400: {"model": FailResponse}},
        status_code=status.HTTP_201_CREATED
        )
async def usersignup(user_data: SignupRequest, db: AsyncSession = Depends(get_session)):
    try:
        new_user = await create_user(user_data=user_data, db=db)
        
        return {
            "message": "회원가입이 성공적으로 완료되었습니다.",
            "data": {"user": new_user}
        }
    except exceptions.UsernameAlreadyExistsError:
        # --- 여기가 핵심 수정 부분 ---
        
        # 1. Pydantic 스키마를 사용해 에러 응답 객체를 생성합니다.
        error_response = schemas.FailResponse(
            status="FAIL",
            error=schemas.ErrorDetail(
                code="USERNAME_ALREADY_EXISTS",
                message="이미 등록된 이메일입니다."
            )
        )
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response.model_dump()
        )
    
@router.post("/login", )
async def userlogin():
    pass

@router.post("/logout", )
async def userlogout():
    pass

@router.delete("/leave",)
async def userleave():
    pass

@router.get("/emails/{email}/exists", response_model=VerifyEmailResponse)
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