from app.user.user_document import UserDocument
from app.user.user_dto import UserData
from app.utils.mongo import db
from dataclasses import asdict


class UserCollection:
    _collection = db["users"]

    @classmethod
    async def create_or_update(cls, user: UserData) -> str:
        """유저 정보를 저장하거나 업데이트 (MongoDB에서 `_id` 자동 생성)"""
        user_dict = asdict(user)
        result = await cls._collection.find_one_and_update(
            {"kakao_id": user.kakao_id}, {"$set": user_dict}, upsert=True, return_document=True  #
        )

        return str(result["_id"])  # ✅ `_id` 반환

    @classmethod
    async def get_by_kakao_id(cls, kakao_id: int) -> UserDocument | None:
        """카카오 ID로 유저 조회"""
        user_data = await cls._collection.find_one({"kakao_id": kakao_id})
        if not user_data:
            return None

        return UserDocument(
            kakao_id=user_data["kakao_id"],
            nickname=user_data["nickname"],
            profile_image=user_data.get("profile_image"),
            thumbnail_image=user_data.get("thumbnail_image"),
            _id=user_data["_id"],  # `_id` 변환
        )
