from urllib.parse import quote
import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport
from pydantic import HttpUrl

from app.main import app


@pytest.mark.asyncio
async def test_get_kakao_code() -> None:
    """카카오 로그인 URL 제공 API 테스트"""
    expected_scope = "profile_nickname, profile_image"
    encoded_scope = quote(expected_scope)  # 공백을 "%20"으로 변환
    expected_auth_url = f"https://kauth.kakao.com/oauth/authorize?response_type=code&client_id=mock_client_id&redirect_uri=mock_redirect_uri&scope={encoded_scope}"

    with patch(
        "app.auth.auth_service.AuthService.getcode_auth_url", return_value=HttpUrl(expected_auth_url)
    ) as mock_getcode_auth_url:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/kakao/authorize")

        assert response.status_code == 200
        assert response.json() == {"auth_url": expected_auth_url}
        mock_getcode_auth_url.assert_called_once_with(expected_scope)


@pytest.mark.asyncio
async def test_kakao_callback() -> None:
    """카카오 OAuth 콜백 API 테스트"""
    mock_code = "mock_code"
    mock_token_info = {"access_token": "mock_access_token"}
    mock_user_data = AsyncMock(
        kakao_id=12345678,
        nickname="Test User",
        profile_image="https://test.com/profile.jpg",
        thumbnail_image="https://test.com/thumbnail.jpg",
    )
    mock_access_jwt = "mock_access_jwt"
    mock_refresh_jwt = "mock_refresh_jwt"

    with (
        patch("app.auth.auth_service.AuthService.get_token", return_value=mock_token_info) as mock_get_token,
        patch("app.auth.auth_service.AuthService.get_user_info", return_value=mock_user_data) as mock_get_user_info,
        patch(
            "app.user.user_service.UserService.create_or_update_user", new_callable=AsyncMock
        ) as mock_create_or_update_user,
        patch(
            "app.utils.jwt_handler.JwtHandler.create_jwt_token", side_effect=[mock_access_jwt, mock_refresh_jwt]
        ) as mock_create_jwt,
    ):

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/kakao/callback?code={mock_code}")

        assert response.status_code == 200
        assert response.json() == {
            "access_token": mock_access_jwt,
            "refresh_token": mock_refresh_jwt,
            "id": 12345678,
            "nickname": "Test User",
            "token_type": "bearer",
            "profile_image": "https://test.com/profile.jpg",
            "thumbnail_image": "https://test.com/thumbnail.jpg",
        }

        mock_get_token.assert_called_once_with(mock_code)
        mock_get_user_info.assert_called_once_with(mock_token_info["access_token"])
        mock_create_or_update_user.assert_awaited_once_with(mock_user_data)
        assert mock_create_jwt.call_count == 2  # Access & Refresh JWT 발급 확인


@pytest.mark.asyncio
async def test_kakao_callback_invalid_code() -> None:
    """카카오 OAuth 콜백 API 테스트 (잘못된 인증 코드)"""
    mock_code = "invalid_code"
    with patch("app.auth.auth_service.AuthService.get_token", return_value={}) as mock_get_token:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/kakao/callback?code={mock_code}")

        assert response.status_code == 400
        assert response.json() == {"detail": "OAuth authentication failed"}
        mock_get_token.assert_called_once_with(mock_code)


@pytest.mark.asyncio
async def test_refresh_token() -> None:
    """리프레시 토큰을 통한 새로운 액세스 토큰 발급 테스트"""
    mock_refresh_token = "mock_refresh_token"
    mock_payload = {"kakao_id": 12345678, "nickname": "Test User"}
    mock_new_access_token = "mock_new_access_jwt"

    with (
        patch(
            "app.utils.jwt_handler.JwtHandler.verify_refresh_token", return_value=mock_payload
        ) as mock_verify_refresh_token,
        patch(
            "app.utils.jwt_handler.JwtHandler.create_jwt_token", return_value=mock_new_access_token
        ) as mock_create_jwt,
    ):

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/kakao/refresh_token", json={"refresh_token": mock_refresh_token})

        assert response.status_code == 200
        assert response.json() == {"access_token": mock_new_access_token, "token_type": "bearer"}
        mock_verify_refresh_token.assert_called_once_with(mock_refresh_token)
        mock_create_jwt.assert_called_once_with({"kakao_id": 12345678, "nickname": "Test User"})


@pytest.mark.asyncio
async def test_refresh_token_invalid() -> None:
    """잘못된 리프레시 토큰으로 요청 시 401 에러 확인"""
    mock_refresh_token = "invalid_refresh_token"

    with patch(
        "app.utils.jwt_handler.JwtHandler.verify_refresh_token", side_effect=ValueError("Invalid token")
    ) as mock_verify_refresh_token:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/kakao/refresh_token", json={"refresh_token": mock_refresh_token})

        assert response.status_code == 401
        assert response.json() == {"detail": "Invalid token"}
        mock_verify_refresh_token.assert_called_once_with(mock_refresh_token)
