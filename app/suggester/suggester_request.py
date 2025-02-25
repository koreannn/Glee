from pydantic import BaseModel


class GenerateSuggestionRequest(BaseModel):
    situation: str
    tone: str | None
    usage: str | None


class SaveSuggestionRequest(BaseModel):
    suggestion: str
    tags: list[str]
