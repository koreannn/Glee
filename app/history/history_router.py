from loguru import logger

from fastapi import APIRouter, Depends

from app.history.history_response import History, GetHistoryResponse
from app.history.history_service import HistoryService
from app.user.user_document import UserDocument
from app.utils.jwt_handler import JwtHandler

router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=GetHistoryResponse)
async def get_history(user: UserDocument = Depends(JwtHandler.get_current_user)) -> GetHistoryResponse:
    logger.info(f"Get history by user: {user.id}")
    histories = await HistoryService.get_histories_by_user(user.id)
    history = [
        History(suggestions=history.suggestions, updated_at=history.updated_at, created_at=history.created_at)
        for history in histories
    ]
    logger.info(f"History: {history}")
    return GetHistoryResponse(history=history)
