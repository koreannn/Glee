from dataclasses import dataclass


@dataclass(kw_only=True, frozen=True)
class UserData:
    kakao_id: str
    nickname: str
    profile_image: str
    thumbnail_image: str
