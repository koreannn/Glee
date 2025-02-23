from dataclasses import dataclass

from app.utils.models.base_document import BaseDocument


@dataclass
class UserDocument(BaseDocument):
    kakao_id: int
    nickname: str
    profile_image: str | None = None
    thumbnail_image: str | None = None
