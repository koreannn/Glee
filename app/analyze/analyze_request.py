from pydantic import BaseModel

from app.analyze.enums import PurposeType


class AnalyzeImagesConversation(BaseModel):
    purpose: PurposeType
