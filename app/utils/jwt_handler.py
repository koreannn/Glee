import datetime
from typing import Any

import jwt

from app.core.settings import settings


class JwtHandler:

    JWT_SECRET = settings.secret_key
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_MINUTES = 60  # JWT 토큰 만료 시간 (1시간)

    @classmethod
    def create_jwt_token(cls, data: dict[Any, Any]) -> str:
        """JWT 토큰 생성"""
        payload = {
            **data,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=cls.JWT_EXPIRATION_MINUTES),
            "iat": datetime.datetime.utcnow(),
        }
        return jwt.encode(payload, cls.JWT_SECRET, algorithm=cls.JWT_ALGORITHM)

    # @classmethod
    # def verify_jwt(cls, token: str) -> dict:
    #     """JWT 검증"""
    #     return jwt.decode(token, cls.JWT_SECRET, algorithms=[cls.JWT_ALGORITHM])

    @classmethod
    def verify_refresh_token(cls, refresh_token: str) -> Any:
        """리프레시 토큰 검증 (성공 시 페이로드 반환, 실패 시 예외 발생)"""
        try:
            payload = jwt.decode(refresh_token, cls.JWT_SECRET, algorithms=[cls.JWT_ALGORITHM])
            return payload  # ✅ 검증된 JWT 데이터 반환
        except jwt.ExpiredSignatureError:
            raise ValueError("Refresh token expired")  # ❌ 만료된 토큰
        except jwt.InvalidTokenError:
            raise ValueError("Invalid refresh token")  # ❌ 잘못된 토큰
