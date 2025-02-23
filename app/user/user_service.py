from app.user.user_collection import UserCollection
from app.user.user_document import UserDocument
from app.user.user_dto import UserData


class UserService:
    """유저 관련 서비스 로직"""

    @classmethod
    async def create_or_update_user(cls, user_data: UserData) -> str:
        """유저 정보를 저장하거나 업데이트"""
        return await UserCollection.create_or_update(user_data)

    @classmethod
    async def get_user_by_kakao_id(cls, kakao_id: int) -> UserDocument | None:
        """카카오 ID로 유저 조회"""
        return await UserCollection.get_by_kakao_id(kakao_id)
