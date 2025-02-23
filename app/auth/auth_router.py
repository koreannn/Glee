from typing import Any

import jwt
from fastapi import APIRouter, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from app.auth.auth_service import AuthService
from fastapi.templating import Jinja2Templates


router = APIRouter(prefix="/kakao", tags=["Kakao OAuth"])



@router.get("/authorize")
async def get_kakao_code():
    """카카오 로그인 URL 제공"""
    scope = "profile_nickname, profile_image"
    return {"auth_url": AuthService.getcode_auth_url(scope)}



@router.get("/callback")
async def kakao_callback(code: str):
    """카카오 OAuth 로그인 후 access_token과 refresh_token 발급"""
    token_info = await AuthService.get_token(code)
    if "access_token" not in token_info:
        raise HTTPException(status_code=400, detail="OAuth authentication failed")

    access_token = token_info["access_token"]
    user_info = await AuthService.get_user_info(access_token)

    if not user_info:
        raise HTTPException(status_code=400, detail="Failed to fetch user info")

    kakao_id = user_info["id"]
    nickname = user_info["kakao_account"]["profile"]["nickname"]

    # 새로운 access_token 및 refresh_token 발급
    access_jwt = AuthService.create_jwt_token({"kakao_id": kakao_id, "nickname": nickname})
    refresh_jwt = AuthService.create_jwt_token({"kakao_id": kakao_id, "nickname": nickname})  # 길게 설정 가능

    return {
        "access_token": access_jwt,
        "refresh_token": refresh_jwt,
        "token_type": "bearer"
    }


@router.post("/refresh_token")
async def refresh_token(refresh_token: str = Form(...)):
    """리프레시 토큰을 사용해 새로운 액세스 토큰을 발급"""
    try:
        payload = jwt.decode(refresh_token, AuthService.JWT_SECRET, algorithms=[AuthService.JWT_ALGORITHM])
        kakao_id = payload["kakao_id"]
        nickname = payload["nickname"]

        # 새로운 access_token 발급
        new_access_token = AuthService.create_jwt_token({"kakao_id": kakao_id, "nickname": nickname})

        return {"access_token": new_access_token, "token_type": "bearer"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
