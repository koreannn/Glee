# from fastapi import UploadFile
#
# from AI.ocr_v2 import clova_ocr, clova_ai_reply_summary
#
#
# class AnalyzeService:
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
