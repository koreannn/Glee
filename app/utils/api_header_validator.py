from typing import Any

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt import PyJWTError
from fastapi import status

from app.core.settings import settings

httpBearer = HTTPBearer(auto_error=False)
JWT_ALGORITHM = "HS256"


def verify_jwt(credentials: HTTPAuthorizationCredentials = Depends(httpBearer)) -> Any:
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    token = credentials.credentials  # 실제 토큰 문자열

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[JWT_ALGORITHM])
        return payload
    except PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")




def optional_verify_jwt(credentials: HTTPAuthorizationCredentials | None = Depends(httpBearer)) -> Any | None:
    if not credentials or not credentials.credentials:
        return None

    token = credentials.credentials  # 실제 토큰 문자열

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[JWT_ALGORITHM])
        return payload
    except PyJWTError:
        return None
