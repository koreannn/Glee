from bson import ObjectId

from app.user.user_document import UserDocument
from app.utils.mongo import db


class UserRepository:
    collection = db["users"]

    @staticmethod
    async def create_or_update(user: UserDocument) -> str:
        """유저 정보를 저장하거나 업데이트"""
        user_dict = user.__dict__.copy()
        user_dict["_id"] = user_dict.get("_id", ObjectId())  # 없으면 새 ObjectId 생성
        existing_user = await UserRepository.collection.find_one({"kakao_id": user.kakao_id})

        if existing_user:
            await UserRepository.collection.update_one({"kakao_id": user.kakao_id}, {"$set": user_dict})
            return str(existing_user["_id"])
        else:
            result = await UserRepository.collection.insert_one(user_dict)
            return str(result.inserted_id)

    @staticmethod
    async def get_by_kakao_id(kakao_id: int) -> UserDocument | None:
        """카카오 ID로 유저 조회"""
        user = await UserRepository.collection.find_one({"kakao_id": kakao_id})
        if user:
            return UserDocument(**user)
        return None
