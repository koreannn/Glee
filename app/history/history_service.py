from datetime import datetime

from bson import ObjectId

from app.history.history_collection import HistoryCollection
from app.history.history_document import HistoryDocument, HistoryDTO
from app.utils.models.suggestion import Suggestion


class HistoryService:

    @staticmethod
    async def create_history(user_id: ObjectId, suggestions: list[Suggestion]) -> HistoryDocument:
        history_dto = HistoryDTO(
            user_id=user_id,
            suggestions=suggestions,
            updated_at=datetime.now(),
            created_at=datetime.now(),
        )
        return await HistoryCollection.create(history_dto)

    @staticmethod
    async def get_histories_by_user(user_id: ObjectId) -> list[HistoryDocument]:
        """특정 사용자의 모든 AI 추천 데이터 가져오기"""
        data_list = await HistoryCollection.get_by_user(user_id)

        history_documents = []
        for data in data_list:
            history_documents.append(
                HistoryDocument(
                    user_id=data["user_id"],
                    suggestions=[
                        Suggestion(title=suggestion_data["title"], content=suggestion_data["content"])
                        for suggestion_data in data["suggestions"]
                    ],
                    updated_at=data["updated_at"],
                    created_at=data["created_at"],
                    _id=data["_id"],
                )
            )

        return history_documents

    @staticmethod
    async def delete_history(history_id: str) -> bool:
        """AI 추천 데이터 삭제"""
        return await HistoryCollection.delete(history_id)
