import sys
import os

from loguru import logger

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# # from AI.services.videosearch_service import VideoSearchService
# from AI.services.Generation.title_suggestion import CLOVA_AI_Title_Suggestions
from AI.services.Generation.reply_seggestion import ReplySuggestion
from AI.services.OCR.get_ocr_text import CLOVA_OCR
from AI.services.Analysis.analyze_situation import CLOVA_AI_Situation_Summary

test_image_files = [
    "./AI/OCR_Testimg.png",
]


# [1] 이미지파일 (최대 4개) 입력 -> 상황을 뱉어내는 함수
def analyze_situation(image_files: list[tuple[str, bytes]]) -> str:
    image2text = CLOVA_OCR(image_files)
    situation_string = CLOVA_AI_Situation_Summary(image2text)
    return situation_string


analyze_situation(test_image_files)

# # -------------------------------------------------------------------
# # [2] 이미지파일 (최대 4개) 입력 -> 상황, 말투, 용도를 뱉어내는 함수
# def analyze_situation_accent_purpose(image_files: list[tuple[str, bytes]]) -> tuple[str, str, str]:
#     image2text = CLOVA_OCR(image_files)
#     situation = CLOVA_AI_Situation_Summary(image2text)
#     accent, purpose = CLOVA_AI_Style_Analysis(image2text)
#     return situation, accent, purpose


# # -------------------------------------------------------------------
# # [3] [1]의 상황을 기반으로 글 제안을 생성하는 함수
# def generate_suggestions_situation(situation: str) -> tuple[list[str], list[str]]:
#     suggestions = CLOVA_AI_Reply_Suggestions(situation)
#     title = CLOVA_AI_Title_Suggestions(situation)
#     return suggestions, title


# # -------------------------------------------------------------------
# # [4] [2]의 상황, 말투, 용도를 기반으로 글 제안을 생성하는 함수
# def generate_reply_suggestions_accent_purpose(situation: str, accent: str, purpose: str) -> tuple[list[str], list[str]]:
#     suggestions = CLOVA_AI_New_Reply_Suggestions(situation, accent, purpose)
#     title = CLOVA_AI_Title_Suggestions(situation)
#     return suggestions, title


# # -------------------------------------------------------------------
# # [5] 상황, 말투, 용도, 상세 설명을 기반으로 글 제안을 생성하는 함수
# def generate_reply_suggestions_detail(
#     situation: str, accent: str, purpose: str, detailed_description: str
# ) -> tuple[list[str], list[str]]:
#     suggestions = CLOVA_AI_New_Reply_Suggestions(situation, accent, purpose, detailed_description)
#     title = CLOVA_AI_Title_Suggestions(situation)
#     return suggestions, title


# """
# youtube 영상 검색 테스트
# """
# # # 로거 설정
# # logger.add("logs/app.log", rotation="500 MB")

# # video_search_service = VideoSearchService()

# # test1: URL로 비디오 ID 추출 테스트
# # test2: 해당 영상이 자막 정보를 제공하는지 여부 확인 동작 테스트
# # test_url = "https://www.youtube.com/watch?v=P9qmSnsyFS0"
# # video_id = video_search_service.extract_video_id(test_url)
# # captions_available = video_search_service.check_captions_available(video_id)
# # logger.info(f"추출된 비디오 ID: {video_id}")
# # logger.info(f"자막 유무 정보: {captions_available}")

# # # test3: 검색 쿼리로 영상 검색 테스트
# # # test4: 영상에 대한 자막 텍스트 추출 테스트
# # test_query = "사과 영양성분"
# # video_info = video_search_service.youtube_search(test_query)
# # video_caption = video_search_service.get_video_transcripts(video_info)
# # logger.info(f"자막 텍스트: {video_caption}")
