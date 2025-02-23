import jwt
import datetime
import httpx
from typing import Any
from app.core.settings import settings


class AuthService:
    client_id = settings.kakao_client_id
    client_secret = settings.kakao_client_secret
    redirect_uri = settings.kakao_redirect_uri
    rest_api_key = settings.kakao_rest_api_key
    logout_redirect_uri = settings.kakao_logout_redirect_uri

    JWT_SECRET = settings.secret_key
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_MINUTES = 60  # JWT 토큰 만료 시간 (1시간)

    @classmethod
    def create_jwt_token(cls, data: dict) -> str:
        """JWT 토큰 생성"""
        payload = {
            **data,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=cls.JWT_EXPIRATION_MINUTES),
            "iat": datetime.datetime.utcnow(),
        }
        return jwt.encode(payload, cls.JWT_SECRET, algorithm=cls.JWT_ALGORITHM)

    @classmethod
    def getcode_auth_url(cls, scope: str) -> str:
        """카카오 OAuth 인증 URL 생성"""
        return f"https://kauth.kakao.com/oauth/authorize?response_type=code&client_id={cls.rest_api_key}&redirect_uri={cls.redirect_uri}&scope={scope}"

    @classmethod
    async def get_token(cls, code: str) -> Any:
        """카카오에서 액세스 토큰 요청"""
        token_request_url = "https://kauth.kakao.com/oauth/token"
        payload = {
            "grant_type": "authorization_code",
            "client_id": cls.client_id,
            "redirect_uri": cls.redirect_uri,
            "code": code,
            "client_secret": cls.client_secret,
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(token_request_url, data=payload)
        return response.json()

    @classmethod
    async def get_user_info(cls, access_token: str) -> dict | None:
        """카카오에서 사용자 정보 요청"""
        userinfo_endpoint = "https://kapi.kakao.com/v2/user/me"
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(userinfo_endpoint, headers=headers)
        return response.json() if response.status_code == 200 else None

    @classmethod
    async def logout(cls, access_token: str) -> None:
        """카카오 로그아웃 요청"""
        logout_url = f"https://kapi.kakao.com/v1/user/logout"
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient() as client:
            await client.post(logout_url)
