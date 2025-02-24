from email.policy import default

from app.auth.auth_service import AuthService
from app.core.settings import settings
import pytest
from unittest.mock import patch


import pytest
from unittest.mock import patch, AsyncMock
from urllib.parse import urlencode

import httpx
from pydantic import HttpUrl

from app.auth.auth_service import AuthService
from app.user.user_dto import UserData
from app.core.settings import settings


@pytest.mark.asyncio
async def test_getcode_auth_url() -> None:
    # given
    expected_scope = "profile_nickname, profile_image"
    expected_url = f"https://kauth.kakao.com/oauth/authorize?{urlencode({'response_type': 'code','client_id': settings.kakao_rest_api_key,'redirect_uri': settings.kakao_redirect_uri,'scope': expected_scope})}"

    # when
    result = AuthService.getcode_auth_url(expected_scope)

    # then
    assert isinstance(result, HttpUrl)
    assert str(result) == expected_url


@pytest.mark.asyncio
async def test_logout() -> None:
    # given
    mock_access_token = "mock_access_token"

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = None  # 응답을 따로 처리하지 않음

        # when
        await AuthService.logout(mock_access_token)

        # then
        mock_post.assert_called_once_with("https://kapi.kakao.com/v1/user/logout")
