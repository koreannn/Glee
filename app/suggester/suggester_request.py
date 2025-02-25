from pydantic import BaseModel

from app.suggester.enums import PurposeType


class AnalyzeImagesConversation(BaseModel):
    purpose: PurposeType


class AnalyzeImagesDetail(BaseModel):
    situation: Image
    tone: str
    usage: str
    purpose: PurposeType


