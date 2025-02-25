from dataclasses import dataclass
from datetime import datetime

from bson import ObjectId

from app.utils.models.base_document import BaseDocument


@dataclass
class SuggesterDocument(BaseDocument):
    user_id: ObjectId
    tag: list[str]
    suggestion: str
    updated_at: datetime
    created_at: datetime


@dataclass(
    kw_only=True,
    frozen=True,
)
class SuggesterDTO:
    user_id: ObjectId
    tag: list[str]
    suggestion: str
    updated_at: datetime
    created_at: datetime
