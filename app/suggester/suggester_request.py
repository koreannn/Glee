from pydantic import BaseModel

from app.core.enums import SuggestionTagType


class GenerateSuggestionRequest(BaseModel):
    situation: str
    tone: str
    usage: str
    detail: str


class SuggestionRequest(BaseModel):
    title: str
    suggestion: str
    tags: list[SuggestionTagType]


class UpdateSuggestionTagsRequest(BaseModel):
    title: str
    suggestion_id: str
    tags: list[SuggestionTagType]
