from fastapi import APIRouter, HTTPException
from app.auth.auth_service import AuthService

from app.user.user_service import UserService
from app.utils.jwt_handler import JwtHandler

router = APIRouter(prefix="/kakao", tags=["Kakao OAuth"])


@router.get("/authorize", response_model=KakaoAuthUrlResponse)
async def get_kakao_code() -> KakaoAuthUrlResponse:
    """카카오 로그인 URL 제공"""
    scope = "profile_nickname, profile_image"
    auth_url = AuthService.getcode_auth_url(scope)
    return KakaoAuthUrlResponse(auth_url=auth_url)


@router.get("/callback")
async def kakao_callback(code: str):
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
    access_jwt = JwtHandler.create_jwt_token({"kakao_id": user_data.kakao_id, "nickname": user_data.nickname})
    refresh_jwt = JwtHandler.create_jwt_token(
        {"kakao_id": user_data.kakao_id, "nickname": user_data.nickname}
    )  # 길게 설정 가능

    return {"access_token": access_jwt, "refresh_token": refresh_jwt, "token_type": "bearer"}


@router.post("/refresh_token", response_model=RefreshTokenResponse)
async def refresh_token(request: KakaoRefreshTokenAuthRequest) -> RefreshTokenResponse:
    """리프레시 토큰을 사용해 새로운 액세스 토큰을 발급"""
    try:
        payload = JwtHandler.verify_refresh_token(request.refresh_token)  # ✅ 서비스 계층에서 검증
        kakao_id = payload["kakao_id"]
        nickname = payload["nickname"]

        # 새로운 access_token 발급
        new_access_token = JwtHandler.create_jwt_token({"kakao_id": kakao_id, "nickname": nickname})

        return RefreshTokenResponse(access_token=new_access_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))  # ❌ 예외 처리
