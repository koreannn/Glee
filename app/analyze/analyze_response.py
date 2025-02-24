from pydantic import BaseModel
from app.analyze.enums import PurposeType


class AnalyzeImagesConversationResponse(BaseModel):
    situation: str
    tone: str
    usage: str
    purpose: PurposeType
