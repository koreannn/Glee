# from fastapi import APIRouter, HTTPException, Request
#
# from app.services.auth_service import AuthService
# from app.core.settings import settings
# from fastapi.responses import RedirectResponse
#
#
# router = APIRouter(prefix="/kakao", tags=["Kakao OAuth"])
#
#
# @router.get("/login")
# async def kakao_login():
#     """카카오 로그인 페이지로 리다이렉트"""
#     client_id = settings.KAKAO_REST_API_KEY
#     redirect_uri = settings.KAKAO_REDIRECT_URI
#     auth_url = (
#         f"https://kauth.kakao.com/oauth/authorize?"
#         f"client_id={client_id}&redirect_uri={redirect_uri}&response_type=code"
#     )
#     return RedirectResponse(auth_url)
#
#
# @router.get("/login/callback")
# async def kakao_callback(request: Request, code: str = None):
#     """카카오 인증 후 콜백 엔드포인트"""
#     if not code:
#         raise HTTPException(status_code=400, detail="No code provided")
#     try:
#         user_data = AuthService.authenticate(code)
#         # TODO: JWT 토큰 생성 후 리다이렉트 또는 JSON 응답
#         return user_data
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))
