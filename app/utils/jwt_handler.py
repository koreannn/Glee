import datetime
from typing import Any
import jwt
from fastapi import HTTPException, Depends

from app.core.settings import settings
from app.user.user_collection import UserCollection
from app.user.user_document import UserDocument
from app.utils.api_header_validator import verify_jwt


class JwtHandler:
    JWT_SECRET = settings.secret_key
    JWT_ALGORITHM = "HS256"

    JWT_EXPIRATION_MINUTES = 600  # JWT 토큰 만료 시간 (1시간)

    @classmethod
    def create_jwt_token(cls, data: dict[Any, Any]) -> str:
        """JWT 토큰 생성"""
        payload = {
            **data,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=cls.JWT_EXPIRATION_MINUTES),
            "iat": datetime.datetime.utcnow(),
        }
        return jwt.encode(payload, cls.JWT_SECRET, algorithm=cls.JWT_ALGORITHM)

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

    @classmethod
    async def get_current_user(cls, payload: dict[Any, Any] = Depends(verify_jwt)) -> UserDocument:
        """JWT 토큰을 이용하여 현재 로그인된 사용자 정보 반환"""
        kakao_id = payload.get("id")

        if not kakao_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        user_document = await UserCollection.get_by_kakao_id(kakao_id)

        if not user_document:
            raise HTTPException(status_code=404, detail="User not found")

        return user_document
