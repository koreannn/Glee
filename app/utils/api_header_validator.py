from typing import Any

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader
from fastapi import status
from jwt import PyJWTError

from app.core.settings import settings

api_key_header = APIKeyHeader(name="Authorization")
JWT_ALGORITHM = "HS256"


def verify_api_header(api_key: str | None = Depends(api_key_header)) -> Any:
    if not api_key:
        # 헤더 자체가 없는 경우
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
        )

    # "Bearer " 접두사 확인
    if not api_key.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format (expected 'Bearer <token>')",
        )

    token = api_key[len("Bearer ") :]  # "Bearer " 제거 → 실제 JWT 토큰
    return token


def verify_jwt(token: str | None = Depends(verify_api_header)) -> Any:

    if token is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[JWT_ALGORITHM])
        return payload
    except PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
