from pydantic import BaseModel
from app.suggester.enums import PurposeType


class AnalyzeImagesConversationResponse(BaseModel):
    situation: str
    tone: str
    usage: str
    purpose: PurposeType



class GenerateSuggestionResponse(BaseModel):
    suggestion: str

