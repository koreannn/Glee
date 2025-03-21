from dataclasses import dataclass
from datetime import datetime

from bson import ObjectId

from app.core.enums import SuggestionTagType
from app.utils.models.base_document import BaseDocument


@dataclass
class SuggesterDocument(BaseDocument):
    user_id: ObjectId
    tag: list[SuggestionTagType]
    title: str
    suggestion: str
    updated_at: datetime
    created_at: datetime
    recommend: bool | None = None


@dataclass(
    kw_only=True,
    frozen=True,
)
class SuggesterDTO:
    user_id: ObjectId
    title: str
    tag: list[str]
    suggestion: str
    updated_at: datetime
    created_at: datetime
    recommend: bool | None = None
