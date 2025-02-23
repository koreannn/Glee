from urllib.parse import urlencode

import httpx
from typing import Any

from pydantic import HttpUrl

from app.core.settings import settings
from app.user.user_dto import UserData


class AuthService:
    client_id = settings.kakao_client_id
    client_secret = settings.kakao_client_secret
    redirect_uri = settings.kakao_redirect_uri
    rest_api_key = settings.kakao_rest_api_key
    logout_redirect_uri = settings.kakao_logout_redirect_uri

    @classmethod
    def getcode_auth_url(cls, scope: str) -> HttpUrl:
        """카카오 OAuth 인증 URL 생성"""
        base_url = "https://kauth.kakao.com/oauth/authorize"
        params = {
            "response_type": "code",
            "client_id": cls.rest_api_key,
            "redirect_uri": cls.redirect_uri,
            "scope": scope,
        }
        print(f"{base_url}?{urlencode(params)}")

        return HttpUrl(f"{base_url}?{urlencode(params)}")

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
    async def get_user_info(cls, access_token: str) -> UserData | None:
        """카카오에서 사용자 정보 요청"""
        userinfo_endpoint = "https://kapi.kakao.com/v2/user/me"
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(userinfo_endpoint, headers=headers)

        data = response.json()
        try:
            user_data = UserData(
                kakao_id=data["id"],
                nickname=data["kakao_account"]["profile"]["nickname"],
                profile_image=data["kakao_account"]["profile"].get("profile_image_url"),
                thumbnail_image=data["kakao_account"]["profile"].get("thumbnail_image_url"),
            )
            return user_data
        except KeyError:
            return None

    @classmethod
    async def logout(cls, access_token: str) -> None:
        """카카오 로그아웃 요청"""
        logout_url = "https://kapi.kakao.com/v1/user/logout"
        # headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient() as client:
            await client.post(logout_url)
