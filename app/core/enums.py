from enum import Enum


class ToneType(Enum):
    WORK = "work"
    SOCIAL = "social"
    FRIENDLY = "friendly"
    LOVELY = "lovely"


class PurposeType(Enum):
    PHOTO_RESPONSE = "Response to photo"
    SIMILAR_VIBE_RESPONSE = "Response with a similar vibe"


class SuggestionTagType(Enum):
    GREETING = "안부"
    COMFORT = "위로"
    CONGRATULATIONS = "축하"
    APOLOGY = "사과"
    GRATITUDE = "감사"
    COMPANY = "회사"
    SCHOOL = "학교"
    REFERENCE = "참고"
    FAVORITES = "즐겨찾기"
    IDEA = "아이디어"
