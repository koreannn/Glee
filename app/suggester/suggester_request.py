from pydantic import BaseModel

from app.core.enums import SuggestionTagType


class GenerateSuggestionRequest(BaseModel):
    situation: str
    tone: str | None
    usage: str | None
    detail: str | None


class SaveSuggestionRequest(BaseModel):
    suggestion: str
    tags: list[SuggestionTagType]


class UpdateSuggestionTagsRequest(BaseModel):
    suggestion_id: str
    tags: list[SuggestionTagType]
