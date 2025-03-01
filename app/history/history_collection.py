from dataclasses import asdict
from typing import Any


from app.history.history_document import HistoryDTO, HistoryDocument
from app.utils.mongo import db
from bson import ObjectId


class HistoryCollection:
    """MongoDB `history` 컬렉션을 관리하는 클래스"""

    _collection = db["history"]

    @classmethod
    async def set_index(cls) -> None:
        """필요한 인덱스 설정"""
        ...

    @classmethod
    async def create(cls, history_dto: HistoryDTO) -> HistoryDocument:
        """MongoDB에 데이터 저장 후 ObjectId 반환"""

        result = await cls._collection.insert_one(asdict(history_dto))

        return HistoryDocument(
            user_id=history_dto.user_id,
            suggestions=history_dto.suggestions,
            created_at=history_dto.created_at,
            updated_at=history_dto.updated_at,
            _id=result.inserted_id,
        )

    @classmethod
    async def get_by_id(cls, history_id: str) -> dict[Any, Any] | None:
        """ID를 기반으로 데이터 조회"""
        return await cls._collection.find_one({"_id": ObjectId(history_id)})

    @classmethod
    async def get_by_user(cls, user_id: ObjectId) -> list[dict[Any, Any]]:
        """사용자의 모든 추천 데이터 조회"""
        cursor = cls._collection.find({"user_id": user_id})
        return await cursor.to_list(length=100)

    @classmethod
    async def delete(cls, history_id: str) -> bool:
        """추천 데이터 삭제"""
        result = await cls._collection.delete_one({"_id": ObjectId(history_id)})
        return result.deleted_count > 0
