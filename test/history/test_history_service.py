import pytest

from app.history.history_document import HistoryDocument
from app.history.history_service import HistoryService
from app.user.user_document import UserDocument
from app.utils.models.suggestion import Suggestion


@pytest.mark.asyncio
async def test_create_history(test_user: UserDocument) -> None:

    user_id = test_user.id
    suggestions = [
        Suggestion(
            title="First test",
            content="First test",
        )
    ]
    history = await HistoryService.create_history(user_id, suggestions)

    assert history.user_id == user_id
    assert history.suggestions == suggestions


@pytest.mark.asyncio
async def test_get_histories_by_user(exists_history: HistoryDocument) -> None:

    history = await HistoryService.get_histories_by_user(exists_history.user_id)

    assert len(history) == 1
    assert history[0].user_id == exists_history.user_id
    assert history[0].suggestions == exists_history.suggestions


@pytest.mark.asyncio
async def test_delete_history(exists_history: HistoryDocument) -> None:
    success = await HistoryService.delete_history(str(exists_history.id))

    assert success == True
    assert await HistoryService.get_histories_by_user(exists_history.user_id) == []
    ...
