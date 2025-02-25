from pydantic import BaseModel


class AuthRequest(BaseModel):
    code: str | None = None  # For handling `/callback` code
    refresh_token: str | None = None  # For handling `/refresh_token` data


class KakaoRefreshTokenAuthRequest(BaseModel):
    refresh_token: str

