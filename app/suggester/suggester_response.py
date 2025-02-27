from datetime import datetime

from pydantic import BaseModel
from app.core.enums import PurposeType, SuggestionTagType


class AnalyzeImagesConversationResponse(BaseModel):
    situation: str
    tone: str
    usage: str
    purpose: PurposeType


class GenerateSuggestionResponse(BaseModel):
    suggestions: list[str]


class SuggestionResponse(BaseModel):
    id: str
    tags: list[SuggestionTagType]
    suggestion: str
    updated_at: datetime
    created_at: datetime


class GetMySuggestionsResponse(BaseModel):
    suggestions: list[SuggestionResponse]


class DeleteSuggestionResponse(BaseModel):
    message: str
    deleted_suggestion_id: str


class PutSuggestionRE(BaseModel):
    suggestions: list[SuggestionResponse]
