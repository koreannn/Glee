def get_user_choice():
    print("사진 첨부 OR 사진 미 첨부")
    print("1. 사진 첨부 (OCR 처리)")
    print("2. 사진 첨부하지 않음 (직접 텍스트 입력)")
    choice = input("선택 (1 또는 2): ")
    return choice.strip()
from loguru import logger

from services.videosearch_service import VideoSearchService

# from ocr_v2 import (
#     analyze_situation_accent_purpose,
#     generate_reply_suggestions_detail,
#     analyze_situation,
# )


# test1: 이미지 -> 상황파악
# Situation(["./OCR_Test1.png","./OCR_Test2.png","./OCR_Test3.png","./OCR_Test4.png"])

# test2: 이미지 -> 상황파악 + 말투 + 용도
# Situation_Accent_Purpose(["./OCR_Test1.png","./OCR_Test2.png","./OCR_Test3.png","./OCR_Test4.png"])

# # test3: 이미지 -> 답변 추천
# print(Reply_Suggestions(["./OCR_Test1.png","./OCR_Test2.png","./OCR_Test3.png","./OCR_Test4.png"]))

# # test4: 상황+말투+용도 -> 새로운 답변 추천
# situation, accent, purpose = Situation_Accent_Purpose(["./OCR_Test1.png","./OCR_Test2.png","./OCR_Test3.png","./OCR_Test4.png"])
# print(New_Reply_Suggestions(situation, accent, purpose))


# # test5: 상황+말투+용도+상세설명 -> 새로운 답변 추천
# situation, accent, purpose = Situation_Accent_Purpose(
#     ["./OCR_Test1.png", "./OCR_Test2.png", "./OCR_Test3.png", "./OCR_Test4.png"]
# )
# logger.info("추가적으로 디테일한 정보 입력:\n")
# detail = input()
# print(New_Reply_Suggestions_Detailed(situation, accent, purpose, detail))

# video_search_service = VideoSearchService()
# video_search_service.youtube_search("바나나")
# rag_service.get_video_transcripts({'id': 'feWQ3yT5ybg', 'title': '사과와 이것 함께 먹었더니 의사들도 놀란 변화가 일어났어요.사과와 상극인 음식. ,다이어트식품,건강음식,사과의 효능,당근의 효능,당뇨음식,혈당,혈관청소음식,노년기 건강.', 'description': '사과와 이것 함께 먹으면 의사들도 깜짝 놀란 변화가 일어납니다. 건강에 좋다는 사과도 잘못 드시면 오히려 건강을 해치는 독이 ...', 'url': 'https://www.youtube.com/watch?v=feWQ3yT5ybg'})
# video_search_service.extract_video_id("https://www.youtube.com/watch?v=yq8JsP-qKVs")


def main():
    # 로거 설정
    logger.add("logs/app.log", rotation="500 MB")

    video_search_service = VideoSearchService()

    # test1: URL로 비디오 ID 추출 테스트
    # test2: 해당 영상이 자막 정보를 제공하는지 여부 확인 동작 테스트
    # test_url = "https://www.youtube.com/watch?v=P9qmSnsyFS0"
    # video_id = video_search_service.extract_video_id(test_url)
    # captions_available = video_search_service.check_captions_available(video_id)
    # logger.info(f"추출된 비디오 ID: {video_id}")
    # logger.info(f"자막 유무 정보: {captions_available}")

    # # test3: 검색 쿼리로 영상 검색 테스트
    # # test4: 영상에 대한 자막 텍스트 추출 테스트
    # test_query = "사과 영양성분"
    # video_info = video_search_service.youtube_search(test_query)
    # video_caption = video_search_service.get_video_transcripts(video_info)
    # logger.info(f"자막 텍스트: {video_caption}")


if __name__ == "__main__":
    main()
# test5: 상황+말투+용도+상세설명 -> 새로운 답변 추천


