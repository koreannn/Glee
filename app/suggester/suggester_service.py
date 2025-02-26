# from fastapi import UploadFile
#
# from AI.ocr_v2 import clova_ocr, clova_ai_reply_summary
#
#
from datetime import datetime

from bson import ObjectId
from fastapi import HTTPException

from AI.ocr_v2 import (
    generate_reply_suggestions_detail,
    generate_reply_suggestions_accent_purpose,
    generate_suggestions_situation,
)
from app.suggester.suggester_collection import SuggesterCollection
from app.suggester.suggester_document import SuggesterDocument, SuggesterDTO


class SuggesterService:
    #
    #     @classmethod
    #     async def extract_situations(cls, images: list[UploadFile]) -> str:
    #         prompt = ""
    #         for image in images:
    #             prompt += clova_ocr(image)
    #
    #         extracted_text = clova_ai_reply_summary(prompt)
    #         return extracted_text
    #
    #     @classmethod
    #     async def analyze_image(cls, image_url: str) -> str:
    #         return ""

    @staticmethod
    async def create_suggestion(user_id: ObjectId, tag: list[str], suggestion: str) -> SuggesterDocument:
        """Suggestion 저장하기"""
        suggestion_dto = SuggesterDTO(
            user_id=user_id,
            tag=tag,
            suggestion=suggestion,
            updated_at=datetime.now(),
            created_at=datetime.now(),
        )
        return await SuggesterCollection.create(suggestion_dto)

    @staticmethod
    async def get_suggestion_by_id(suggestion_id: str) -> SuggesterDocument:
        """ID를 기반으로 AI 추천 데이터 가져오기"""
        data = await SuggesterCollection.get_by_id(suggestion_id)
        if data is None or not data:
            raise HTTPException(status_code=404, detail="Suggestion not found")

        return SuggesterDocument(**data)

    @staticmethod
    async def get_suggestions_by_user(user_id: ObjectId) -> list[SuggesterDocument]:
        """특정 사용자의 모든 AI 추천 데이터 가져오기"""
        data_list = await SuggesterCollection.get_by_user(user_id)
        return [SuggesterDocument(**data) for data in data_list]

    @staticmethod
    async def delete_suggestion(suggestion_id: str) -> bool:
        """AI 추천 데이터 삭제"""
        return await SuggesterCollection.delete(suggestion_id)

    @staticmethod
    async def generate_suggestions(
        situation: str, tone: str | None = None, usage: str | None = None, detail: str | None = None
    ) -> list[str]:
        if situation and tone and usage and detail:
            suggestions = generate_reply_suggestions_detail(situation, tone, usage, detail)
        elif situation and tone and usage:
            suggestions = generate_reply_suggestions_accent_purpose(situation, tone, usage)
        elif situation:
            suggestions = generate_suggestions_situation(situation)
        else:
            raise HTTPException(status_code=400, detail="Invalid Generate Suggestion Request")
        return suggestions
