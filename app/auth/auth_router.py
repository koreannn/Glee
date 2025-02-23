from typing import Any

from fastapi import APIRouter, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from app.auth.auth_service import AuthService
from fastapi.templating import Jinja2Templates

from app.auth.schemas import KakaoAuthUrl

router = APIRouter(prefix="/kakao", tags=["Kakao OAuth"])

# Jinja2 템플릿 엔진을 설정
templates = Jinja2Templates(directory="templates")


# 카카오 로그인을 시작하기 위한 엔드포인트
@router.get("/authorize", response_model=KakaoAuthUrl)
def get_kakao_code(request: Request) -> RedirectResponse:
    scope = "profile_nickname, profile_image"  # 요청할 권한 범위
    kakao_auth_url = AuthService.getcode_auth_url(scope)
    return RedirectResponse(kakao_auth_url)


# 카카오 로그인 후 카카오에서 리디렉션될 엔드포인트
# 카카오에서 제공한 인증 코드를 사용하여 액세스 토큰을 요청
@router.get("/callback")
async def kakao_callback(request: Request, code: str) -> RedirectResponse:
    token_info = await AuthService.get_token(code)
    if "access_token" in token_info:
        request.session["access_token"] = token_info["access_token"]
        print("로그인 성공")
        return RedirectResponse(url="/kakao/user_info", status_code=302)
    else:
        return RedirectResponse(url="/?error=Failed to authenticate", status_code=302)


# 홈페이지 및 로그인/로그아웃 버튼을 표시
@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request) -> HTMLResponse:
    logged_in = False
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "client_id": AuthService.client_id,
            "redirect_uri": AuthService.redirect_uri,
            "logged_in": logged_in,
        },
    )


# 로그아웃 처리를 위한 엔드포인트
# 세션에서 액세스 토큰을 제거하고 홈페이지로 리다이렉트
@router.get("/logout")
async def logout(request: Request) -> RedirectResponse:
    client_id = AuthService.client_id
    logout_redirect_uri = AuthService.logout_redirect_uri
    await AuthService.logout(client_id, logout_redirect_uri)
    request.session.pop("access_token", None)
    return RedirectResponse(url="/")


# 사용자 정보를 표시하기 위한 엔드포인트
# 세션에 저장된 액세스 토큰을 사용하여 카카오 API에서 사용자 정보를 가져옴
@router.get("/user_info", response_class=HTMLResponse)
async def user_info(request: Request) -> HTMLResponse:
    access_token = request.session.get("access_token")
    if access_token:
        user_info = await AuthService.get_user_info(access_token)
        return templates.TemplateResponse("user_info.html", {"request": request, "user_info": user_info})
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")


# 액세스 토큰을 새로고침하기 위한 엔드포인트
@router.post("/refresh_token")
async def refresh_token(refresh_token: str = Form(...)) -> Any:
    client_id = AuthService.client_id
    new_token_info = await AuthService.refreshAccessToken(client_id, refresh_token)
    return new_token_info
