import sys
import os

from loguru import logger

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# # from AI.services.videosearch_service import VideoSearchService
# from AI.services.Generation.title_suggestion import CLOVA_AI_Title_Suggestions
from AI.services.Generation.reply_seggestion import ReplySuggestion
from AI.services.OCR.get_ocr_text import CLOVA_OCR
from AI.services.Analysis.analyze_situation import Analyze
from AI.services.Generation.title_suggestion import TitleSuggestion

test_image_files = ["./AI/OCR_Test1.png", "./AI/OCR_Test2.png", "./AI/OCR_Test3.png", "./AI/OCR_Test4.png"]
situation_service = Analyze()
reply_service = ReplySuggestion()
title_service = TitleSuggestion()
# [1] 이미지파일 (최대 4개) 입력 -> 상황을 뱉어내는 함수
def analyze_situation(image_files: list[str]) -> str:
    # 이미지 파일들을 읽어서 튜플 리스트로 변환
    image2text = CLOVA_OCR(image_files)
    situation = situation_service.situation_summary(image2text)
    return situation

analyze_situation(test_image_files)

# -------------------------------------------------------------------
# [2] 이미지파일 (최대 4개) 입력 -> 상황, 말투, 용도를 뱉어내는 함수
def analyze_situation_accent_purpose(image_files: list[tuple[str, bytes]]) -> tuple[str, str, str]:
    image_tuples = []
    for file_path in image_files:
        with open(file_path, 'rb') as f:
            image_data = f.read()
            image_tuples.append((file_path, image_data))
            
    image2text = CLOVA_OCR(image_tuples)
    situation = situation_service.situation_summary(image2text)
    accent, purpose = situation_service.style_analysis(image2text)
    return situation, accent, purpose
analyze_situation_accent_purpose(test_image_files)


-------------------------------------------------------------------
[3] [1]의 상황을 기반으로 글 제안을 생성하는 함수
def generate_suggestions_situation(situation: str) -> tuple[list[str], list[str]]:
    suggestions = reply_service.generate_basic_reply(situation)
    title = title_service._generate_title_suggestions(situation)
    return suggestions, title
situation = situation_service.situation_summary(CLOVA_OCR(test_image_files))
generate_suggestions_situation(situation)

# -------------------------------------------------------------------
# [4] [2]의 상황, 말투, 용도를 기반으로 글 제안을 생성하는 함수
def generate_reply_suggestions_accent_purpose(situation: str, accent: str, purpose: str) -> tuple[list[str], list[str]]:
    suggestions = reply_service.generate_detailed_reply(situation, accent, purpose)
    title = title_service._generate_title_suggestions(situation)
    return suggestions, title
situation = situation_service.situation_summary(CLOVA_OCR(test_image_files))
generate_reply_suggestions_accent_purpose(situation, "귀엽고 사랑스러운 말투", "카카오톡")

# -------------------------------------------------------------------
# [5] 상황, 말투, 용도, 상세 설명을 기반으로 글 제안을 생성하는 함수
def generate_reply_suggestions_detail(
    situation: str, accent: str, purpose: str, detailed_description: str
) -> tuple[list[str], list[str]]:
    suggestions = reply_service.generate_detailed_reply(situation, accent, purpose, detailed_description)
    title = title_service._generate_title_suggestions(situation)
    return suggestions, title
situation = situation_service.situation_summary(CLOVA_OCR(test_image_files))
generate_reply_suggestions_detail(situation, "귀엽고 사랑스러운 말투", "카카오톡", "친구들과 함께 카카오톡을 사용하는 경우")

"""
youtube 영상 검색 테스트
"""
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



