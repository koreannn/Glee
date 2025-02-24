from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi import status
from pydantic import HttpUrl

from app.auth.auth_request import KakaoRefreshTokenAuthRequest
from app.auth.auth_response import (
    KakaoCallbackResponse,
    RefreshTokenResponse,
    KakaoAuthUrlResponse,
    CurrentUserResponse,
)
from app.auth.auth_service import AuthService
from app.user.user_document import UserDocument

from app.user.user_service import UserService
from app.utils.jwt_handler import JwtHandler
from app.utils.jwt_payload import JwtPayload

router = APIRouter(prefix="/kakao", tags=["Kakao OAuth"])


@router.get("/authorize", response_model=KakaoAuthUrlResponse)
async def get_kakao_code() -> KakaoAuthUrlResponse:
    """카카오 로그인 URL 제공"""
    scope = "profile_nickname, profile_image"
    auth_url = AuthService.getcode_auth_url(scope)
    return KakaoAuthUrlResponse(auth_url=auth_url)


@router.get("/callback", response_model=KakaoCallbackResponse)
async def kakao_callback(code: str = Query(..., description="카카오 OAuth 인증 코드")) -> KakaoCallbackResponse:
    """카카오 OAuth 로그인 후 access_token과 refresh_token 발급"""
    token_info = await AuthService.get_token(code)
    if "access_token" not in token_info:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OAuth authentication failed")

    access_token = token_info["access_token"]
    user_data = await AuthService.get_user_info(access_token)

    if not user_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to fetch user info")

    await UserService.create_or_update_user(user_data)

    # 새로운 access_token 및 refresh_token 발급
    payload = JwtPayload(id=int(user_data.kakao_id), nickname=user_data.nickname)

    access_jwt = JwtHandler.create_jwt_token(payload.model_dump())
    refresh_jwt = JwtHandler.create_jwt_token(payload.model_dump())  # 길게 설정 가능

    return KakaoCallbackResponse(
        access_token=access_jwt,
        refresh_token=refresh_jwt,
        id=int(user_data.kakao_id),
        nickname=user_data.nickname,
        profile_image=HttpUrl(user_data.profile_image),
        thumbnail_image=HttpUrl(user_data.thumbnail_image),
    )


@router.post("/refresh_token", response_model=RefreshTokenResponse)
async def refresh_token(request: KakaoRefreshTokenAuthRequest) -> RefreshTokenResponse:
    """리프레시 토큰을 사용해 새로운 액세스 토큰을 발급"""
    try:
        payload = JwtHandler.verify_refresh_token(request.refresh_token)  # ✅ 서비스 계층에서 검증
        kakao_id = payload["id"]
        nickname = payload["nickname"]

        # 새로운 access_token 발급
        new_access_token = JwtHandler.create_jwt_token({"id": kakao_id, "nickname": nickname})

        return RefreshTokenResponse(access_token=new_access_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))  # ❌ 예외 처리


@router.get("/me", response_model=CurrentUserResponse)
async def get_current_user(user: UserDocument = Depends(JwtHandler.get_current_user)) -> CurrentUserResponse:
    """JWT 토큰을 기반으로 현재 로그인한 유저 정보 반환"""
    print("auth router get_current_user", user.id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return CurrentUserResponse(
        id=user.kakao_id,
        nickname=user.nickname,
        profile_image=user.profile_image,
        thumbnail_image=user.thumbnail_image,
    )
