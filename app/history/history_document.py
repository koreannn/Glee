from dataclasses import dataclass
from datetime import datetime

from bson import ObjectId


from app.utils.models.base_document import BaseDocument
from app.utils.models.suggestion import Suggestion


@dataclass
class HistoryDocument(BaseDocument):
    user_id: ObjectId
    suggestions: list[Suggestion]
    updated_at: datetime
    created_at: datetime


@dataclass(kw_only=True)
class HistoryDTO:
    user_id: ObjectId
    suggestions: list[Suggestion]
    updated_at: datetime
    created_at: datetime
