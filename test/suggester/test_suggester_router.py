import pytest
from unittest.mock import patch, AsyncMock
from bson import ObjectId
from httpx import AsyncClient, ASGITransport

from app.core.settings import settings
from app.main import app


@pytest.fixture
def auth_headers():
    """테스트용 JWT 인증 헤더 생성"""
    return {"Authorization": f"Bearer {settings.test_jwt_token}"}


@pytest.mark.asyncio
async def test_save_suggestion(auth_headers):
    """유저가 생성한 AI 글제안 - 저장"""
    data = {"tags": ["AI", "Machine Learning"], "suggestion": "This is a test suggestion"}

    with patch(
        "app.suggester.suggester_service.SuggesterService.create_suggestion", new_callable=AsyncMock
    ) as mock_create_suggestion:
        mock_create_suggestion.return_value = AsyncMock(
            id=ObjectId(),
            tag=data["tags"],
            suggestion=data["suggestion"],
            updated_at="2024-02-25T12:00:00",
            created_at="2024-02-25T12:00:00",
        )

        # noinspection PyUnresolvedReferences
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:  # ✅ 비동기 클라이언트 사용
            response = await client.post("/suggester/", json=data, headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["suggestion"] == data["suggestion"]
    assert "id" in response.json()


@pytest.mark.asyncio
async def test_get_suggestion(auth_headers):
    """ID를 기반으로 AI 추천 데이터 가져오기"""
    mock_suggestion_id = str(ObjectId())

    with patch(
        "app.suggester.suggester_service.SuggesterService.get_suggestion_by_id", new_callable=AsyncMock
    ) as mock_get_suggestion:
        mock_get_suggestion.return_value = AsyncMock(
            id=mock_suggestion_id,
            tag=["AI", "NLP"],
            suggestion="Test suggestion",
            updated_at="2024-02-25T12:00:00",
            created_at="2024-02-25T12:00:00",
        )

        response = client.get(f"/suggester/{mock_suggestion_id}", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["id"] == mock_suggestion_id
    assert response.json()["suggestion"] == "Test suggestion"


@pytest.mark.asyncio
async def test_get_my_suggestions(auth_headers):
    """현재 사용자의 모든 추천 데이터 가져오기"""
    with patch(
        "app.suggester.suggester_service.SuggesterService.get_suggestions_by_user", new_callable=AsyncMock
    ) as mock_get_my_suggestions:
        mock_get_my_suggestions.return_value = [
            AsyncMock(
                id=ObjectId(),
                tag=["AI"],
                suggestion="First test",
                updated_at="2024-02-25T12:00:00",
                created_at="2024-02-25T12:00:00",
            ),
            AsyncMock(
                id=ObjectId(),
                tag=["Python"],
                suggestion="Second test",
                updated_at="2024-02-25T12:00:00",
                created_at="2024-02-25T12:00:00",
            ),
        ]

        response = client.get("/suggester/user/me", headers=auth_headers)

    assert response.status_code == 200
    assert len(response.json()["suggestions"]) == 2


@pytest.mark.asyncio
async def test_delete_suggestion(auth_headers):
    """추천 데이터 삭제 테스트"""
    mock_suggestion_id = str(ObjectId())

    with (
        patch(
            "app.suggester.suggester_service.SuggesterService.get_suggestion_by_id", new_callable=AsyncMock
        ) as mock_get_suggestion,
        patch(
            "app.suggester.suggester_service.SuggesterService.delete_suggestion", new_callable=AsyncMock
        ) as mock_delete_suggestion,
    ):

        mock_get_suggestion.return_value = AsyncMock(
            id=mock_suggestion_id,
            tag=["AI", "NLP"],
            suggestion="To be deleted",
            updated_at="2024-02-25T12:00:00",
            created_at="2024-02-25T12:00:00",
        )
        mock_delete_suggestion.return_value = True  # 삭제 성공

        response = client.delete(f"/suggester/{mock_suggestion_id}", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["message"] == "Suggestion deleted successfully"
