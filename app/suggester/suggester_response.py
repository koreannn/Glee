from datetime import datetime

from pydantic import BaseModel
from app.core.enums import PurposeType, SuggestionTagType


class AnalyzeImagesConversationResponse(BaseModel):
    situation: str
    tone: str
    usage: str
    purpose: PurposeType


class GenerateSuggestion(BaseModel):
    title: str
    content: str


class GenerateSuggestionsResponse(BaseModel):
    suggestions: list[GenerateSuggestion]


class SuggestionResponse(BaseModel):
    id: str
    title: str
    tags: list[SuggestionTagType]
    suggestion: str
    updated_at: datetime
    created_at: datetime


class SuggestionsResponse(BaseModel):
    suggestions: list[SuggestionResponse]


class SuggestionSummary(BaseModel):
    title: str
    content: str


class SuggestionsSummaryResponse(BaseModel):
    suggestions: list[SuggestionSummary]


class DeleteSuggestionResponse(BaseModel):
    message: str
    deleted_suggestion_id: str


class PutSuggestionResponse(BaseModel):
    suggestions: list[SuggestionResponse]
