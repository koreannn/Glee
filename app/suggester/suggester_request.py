from pydantic import BaseModel


class GenerateSuggestionRequest(BaseModel):
    situation: str
    tone: str | None
    usage: str | None
