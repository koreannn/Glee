from typing import Optional

from pydantic import BaseModel, HttpUrl


class KakaoAuthUrlResponse(BaseModel):
    """카카오 로그인 URL 응답 DTO"""

    auth_url: HttpUrl


class KakaoCallbackResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    nickname: str
    id: int
    profile_image: Optional[HttpUrl]
    thumbnail_image: Optional[HttpUrl]


class RefreshTokenResponse(BaseModel):
    """리프레시 토큰 응답 DTO"""

    access_token: str
    token_type: str = "bearer"


class CurrentUserResponse(BaseModel):
    id: int
    nickname: str
    profile_image: str
    thumbnail_image: str
