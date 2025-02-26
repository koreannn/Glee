from pathlib import Path

import pytest
from unittest.mock import patch, AsyncMock
from bson import ObjectId
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.suggester.enums import PurposeType
from app.suggester.suggester_document import SuggesterDocument


@pytest.mark.asyncio
async def test_save_suggestion(auth_header: dict[str, str]) -> None:
    """유저가 생성한 AI 글제안 - 저장"""

    from app.suggester.suggester_request import SaveSuggestionRequest

    data = SaveSuggestionRequest(tags=["AI", "Machine Learning"], suggestion="This is a test suggestion").model_dump()

    with patch(
        "app.suggester.suggester_service.SuggesterService.create_suggestion", new_callable=AsyncMock
    ) as mock_create_suggestion:
        mock_create_suggestion.return_value = AsyncMock(
            id=str(ObjectId()),
            tag=data["tags"],
            suggestion=data["suggestion"],
            updated_at="2024-02-25T12:00:00",
            created_at="2024-02-25T12:00:00",
        )

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/suggester/", json=data, headers=auth_header)

    assert response.status_code == 200
    assert response.json()["suggestion"] == data["suggestion"]
    assert "id" in response.json()


@pytest.mark.asyncio
async def test_get_suggestion(exists_suggestion: SuggesterDocument, auth_header: dict[str, str]) -> None:
    """ID를 기반으로 AI 추천 데이터 가져오기"""

    with patch(
        "app.suggester.suggester_service.SuggesterService.get_suggestion_by_id", new_callable=AsyncMock
    ) as mock_get_suggestion:
        mock_get_suggestion.return_value = AsyncMock(
            id=exists_suggestion.id,
            user_id=exists_suggestion.user_id,
            tag=exists_suggestion.tag,
            suggestion=exists_suggestion.suggestion,
            updated_at=exists_suggestion.updated_at,
            created_at=exists_suggestion.created_at,
        )

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/suggester/{exists_suggestion.id}", headers=auth_header)

    assert response.status_code == 200
    assert response.json()["id"] == str(exists_suggestion.id)
    assert response.json()["suggestion"] == "Test suggestion"


@pytest.mark.asyncio
async def test_get_my_suggestions(auth_header: dict[str, str]) -> None:
    """현재 사용자의 모든 추천 데이터 가져오기"""
    with patch(
        "app.suggester.suggester_service.SuggesterService.get_suggestions_by_user", new_callable=AsyncMock
    ) as mock_get_my_suggestions:
        mock_get_my_suggestions.return_value = [
            AsyncMock(
                id=str(ObjectId()),
                tag=["AI"],
                suggestion="First test",
                updated_at="2024-02-25T12:00:00",
                created_at="2024-02-25T12:00:00",
            ),
            AsyncMock(
                id=str(ObjectId()),
                tag=["Python"],
                suggestion="Second test",
                updated_at="2024-02-25T12:00:00",
                created_at="2024-02-25T12:00:00",
            ),
        ]

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/suggester/user/me", headers=auth_header)

    assert response.status_code == 200
    assert len(response.json()["suggestions"]) == 2


@pytest.mark.asyncio
async def test_delete_suggestion(exists_suggestion: SuggesterDocument, auth_header: dict[str, str]) -> None:
    """추천 데이터 삭제 테스트"""
    with (
        patch(
            "app.suggester.suggester_service.SuggesterService.get_suggestion_by_id", new_callable=AsyncMock
        ) as mock_get_suggestion,
        patch(
            "app.suggester.suggester_service.SuggesterService.delete_suggestion", new_callable=AsyncMock
        ) as mock_delete_suggestion,
    ):
        mock_get_suggestion.return_value = AsyncMock(
            id=exists_suggestion.id,
            tag=exists_suggestion.tag,
            user_id=exists_suggestion.user_id,
            suggestion=exists_suggestion.suggestion,
            updated_at=exists_suggestion.updated_at,
            created_at=exists_suggestion.created_at,
        )

        mock_delete_suggestion.return_value = True  # 삭제 성공

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.delete(f"/suggester/{str(exists_suggestion.id)}", headers=auth_header)

    assert response.status_code == 200
    assert response.json()["message"] == "Suggestion deleted successfully"


@pytest.mark.asyncio
async def test_analyze_images_to_response_to_photo(test_image_path: Path, auth_header: dict[str, str]) -> None:

    # 파일을 바이너리 모드로 읽기
    with open(test_image_path, "rb") as f:
        image_data = f.read()

    # 업로드할 파일 리스트
    files = {
        "image_file_1": ("test_image.jpg", image_data, "image/png"),
        "image_file_2": ("test_image.jpg", image_data, "image/png"),
    }
    purpose_value = str(PurposeType.PHOTO_RESPONSE.value)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/suggester/analyze/image", files=files, data={"purpose": purpose_value}, headers=auth_header
        )

    assert response.status_code == 200
    assert response.json()["purpose"] == PurposeType.PHOTO_RESPONSE.value
    assert response.json()["tone"] == ""
    assert response.json()["usage"] == ""


@pytest.mark.asyncio
async def test_analyze_images_to_similar_vibe(test_image_path: Path, auth_header: dict[str, str]) -> None:

    # 파일을 바이너리 모드로 읽기
    with open(test_image_path, "rb") as f:
        image_data = f.read()

    # 업로드할 파일 리스트
    files = {
        "image_file_1": ("test_image.jpg", image_data, "image/png"),
        "image_file_2": ("test_image.jpg", image_data, "image/png"),
    }
    purpose_value = str(PurposeType.SIMILAR_VIBE_RESPONSE.value)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/suggester/analyze/image", files=files, data={"purpose": purpose_value}, headers=auth_header
        )

    assert response.status_code == 200
    assert response.json()["purpose"] == PurposeType.SIMILAR_VIBE_RESPONSE.value
    assert response.json()["tone"] != ""
    assert response.json()["usage"] != ""
