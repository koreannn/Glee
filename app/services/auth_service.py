# from fastapi import requests
# from sqlalchemy.orm import Session
#
# from app.core.settings import settings
# from app.db.database import SessionLocal
#
#
# class KakaoService:
#     @classmethod
#     def get_access_token(cls, code: str) -> dict:
#         data = {
#             "grant_type": "authorization_code",
#             "client_id": settings.KAKAO_REST_API_KEY,
#             "client_secret": settings.KAKAO_CLIENT_SECRET,
#             "redirect_uri": settings.KAKAO_REDIRECT_URI,
#             "code": code,
#         }
#         response = requests.post("https://kauth.kakao.com/oauth/token", data=data)
#         if response.status_code != 200:
#             raise Exception("Failed to get access token from Kakao")
#         return response.json()
#
#     @classmethod
#     def get_user_info(cls, access_token: str) -> dict:
#         headers = {
#             "Authorization": f"Bearer {access_token}",
#             "Content-type": "application/x-www-form-urlencoded;charset=utf-8",
#         }
#         response = requests.get("https://kapi.kakao.com/v2/user/me", headers=headers)
#         if response.status_code != 200:
#             raise Exception("Failed to get user info from Kakao")
#         return response.json()
#
#     @classmethod
#     def authenticate(cls, code: str) -> dict:
#         token_data = cls.get_access_token(code)
#         access_token = token_data.get("access_token")
#         if not access_token:
#             raise Exception("No access token received")
#         user_info = cls.get_user_info(access_token)
#
#         kakao_id = str(user_info.get("id"))
#         kakao_account = user_info.get("kakao_account", {})
#         email = kakao_account.get("email")
#         profile = kakao_account.get("profile", {})
#         nickname = profile.get("nickname")
#
#         # DB 저장
#         db: Session = SessionLocal()
#         user = db.query(User).filter(User.kakao_id == kakao_id).first()
#         if not user:
#             user = User(kakao_id=kakao_id, email=email, nickname=nickname)
#             db.add(user)
#             db.commit()
#             db.refresh(user)
#         else:
#             # 필요한 경우 업데이트
#             user.email = email
#             user.nickname = nickname
#             db.commit()
#         db.close()
#
#         # 반환 예시 (추후 JWT 토큰 발급 등 추가 가능)
#         return {
#             "kakao_id": kakao_id,
#             "email": email,
#             "nickname": nickname,
#             "access_token": access_token,
#         }
