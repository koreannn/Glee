# from datetime import datetime, timedelta, timezone
# import time
# from typing import Optional
#
# from fastapi import Depends, HTTPException
# from fastapi.security import OAuth2PasswordBearer
# from jose import ExpiredSignatureError, jwt, JWTError
#
# from app.core.settings import settings
# from app.dtos.user.auth import GoogleUserInfo, JWTDecodedInfo
#
#
# class JWTHandler:
#     SECRET_KEY = settings.SECRET_KEY
#     ALGORITHM = "HS256"
#     ACCESS_TOKEN_EXPIRE_MINUTES = 43200
#
#     # auto_error: 401 에러 자동 발생 여부. False시 에러 발생했을 때 None을 반환
#     # False해서 로그인을 하지 않았을 때, 자동으로 에러가 발생되지 않도록 구현
#     oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)
#
#     @classmethod
#     def create_access_token(
#         cls, user_info: GoogleUserInfo, expires_delta: Optional[timedelta] = None
#     ) -> str:
#         if expires_delta:
#             expire = datetime.now(timezone.utc) + expires_delta
#         else:
#             expire = datetime.now(timezone.utc) + timedelta(
#                 minutes=cls.ACCESS_TOKEN_EXPIRE_MINUTES
#             )
#
#         to_encode = {"sub": user_info.email, "exp": expire}
#
#         # JWT 인코딩
#         encoded_jwt = jwt.encode(to_encode, cls.SECRET_KEY, algorithm=cls.ALGORITHM)
#
#         return encoded_jwt
#
#     @classmethod
#     def get_current_user(
#         cls, token: str | None = Depends(oauth2_scheme)
#     ) -> JWTDecodedInfo:
#         return cls._verify_token(token)
#
#     @classmethod
#     def optional_get_current_user(
#         cls, token: str | None = Depends(oauth2_scheme)
#     ) -> JWTDecodedInfo | None:
#         """
#         유저 로그인 여부를 선택적으로 확인할 때 사용하는 함수
#         (로그인하지 않아도 볼 수 있는 페이지에서 사용)
#         유저 정보가 없을 때 None 반환
#         """
#         return cls._optional_verify_token(token)
#
#     @classmethod
#     def _verify_token(
#         cls, token: str | None = Depends(oauth2_scheme)
#     ) -> JWTDecodedInfo:
#         # Authorization이 없을 때 에러 발생
#         if token is None:
#             raise HTTPException(
#                 status_code=401,
#                 detail="Could not validate credentials",
#                 headers={"WWW-Authenticate": "Bearer"},
#             )
#
#         # dev test용 계정
#         if token == "dev_test_token":
#             return JWTDecodedInfo(
#                 sub="dev@test.com",
#                 exp=int(time.time()) + cls.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
#             )
#
#         try:
#             payload = jwt.decode(token, cls.SECRET_KEY, algorithms=[cls.ALGORITHM])
#         except ExpiredSignatureError:
#             raise HTTPException(
#                 status_code=401,
#                 detail="Token expired",
#                 headers={"WWW-Authenticate": "Bearer"},
#             )
#
#         except JWTError:
#             raise HTTPException(
#                 status_code=401,
#                 detail="Invalid token",
#                 headers={"WWW-Authenticate": "Bearer"},
#             )
#
#         return JWTDecodedInfo.model_validate(payload)
#
#     @classmethod
#     def _optional_verify_token(
#         cls, token: str | None = Depends(oauth2_scheme)
#     ) -> JWTDecodedInfo | None:
#         """
#         유저 로그인 여부를 선택적으로 확인할 때 사용하는 함수
#         (로그인하지 않아도 볼 수 있는 페이지에서 사용)
#         _verify_token이랑 다른 점은 토큰이 유효하지 않을 때 Exception이 발생하지 않고 None을 반환한다.
#         """
#         # 토큰이 없는 경우 None 반환
#         if token is None:
#             return None
#
#         # 토큰이 있는 경우 토큰 검증 (실패하면 None 반환)
#         try:
#             decoded_info = cls._verify_token(token)
#             return decoded_info
#         except (ExpiredSignatureError, JWTError):
#             return None
