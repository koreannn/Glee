from datetime import datetime

from pydantic import BaseModel
from app.suggester.enums import PurposeType


class AnalyzeImagesConversationResponse(BaseModel):
    situation: str
    tone: str
    usage: str
    purpose: PurposeType


class GenerateSuggestionResponse(BaseModel):
    suggestion: str


class SuggestionResponse(BaseModel):
    id: str
    tags: list[str]
    suggestion: str
    updated_at: datetime
    created_at: datetime


class GetMySuggestionsResponse(BaseModel):
    suggestions: list[SuggestionResponse]


class DeleteSuggestionResponse(BaseModel):
    message: str
    deleted_suggestion_id: str
