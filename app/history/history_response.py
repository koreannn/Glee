from datetime import datetime

from pydantic import BaseModel

from app.utils.models.suggestion import Suggestion



class History(BaseModel):
    suggestions: list[Suggestion]
    updated_at: datetime
    created_at: datetime


class GetHistoryResponse(BaseModel):
    history: list[History]

