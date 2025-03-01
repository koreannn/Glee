def get_user_choice():
    print("사진 첨부 OR 사진 미 첨부")
    print("1. 사진 첨부 (OCR 처리)")
    print("2. 사진 첨부하지 않음 (직접 텍스트 입력)")
    choice = input("선택 (1 또는 2): ")
    return choice.strip()
from loguru import logger

from services.videosearch_service import VideoSearchService

from ocr_v2 import (
    CLOVA_AI_Situation_Summary,
    CLOVA_AI_Title_Suggestions,
    CLOVA_AI_Reply_Suggestions,
    CLOVA_AI_New_Reply_Suggestions,
    CLOVA_AI_Style_Analysis,

    analyze_situation,
    analyze_situation_accent_purpose,
    generate_suggestions_situation,
    generate_reply_suggestions_accent_purpose,
    New_Reply_Suggestions_Detailed,
)
from services.title_suggestion import CLOVA_AI_Title_Suggestions


def main():
    # # 1. 개별 메서드 출력 테스트
    # CLOVA_AI_Situation_Summary("아, 배고프다.")
    # CLOVA_AI_Title_Suggestions("아, 배고프다.")
    # CLOVA_AI_Reply_Suggestions("식사 시간이 다가오면 배고픔을 느끼는 것은 자연스러운 일이죠. 식사를 할 수 없는 상황이라면 간단한 간식이나 음료를 섭취하여 급한 배고픔을 해결할 수도 있습니다. 만약 지속적인 배고픔 때문에 고민이시라면 건강 상태나 생활 습관을 한 번 되돌아보시는 건 어떠신가요?")
    # CLOVA_AI_New_Reply_Suggestions("배고픈 상황", "친절하게", "카카오톡", "친절하지만 퉁명스럽게 말해주세요" )
    CLOVA_AI_Style_Analysis("아, 배고프다.")
    # CLOVA_AI_Title_Suggestions("식사 시간이 되었다면, 건강하고 맛있는 식사를 챙겨 드시는 것은 어떠신가요?식사 시간이 되었다면, 건강하고 맛있는 식사를 챙겨 드시는 것은 어떠신가요?")

    # generate_suggestions_situation("아, 자고싶다.")
    # generate_reply_suggestions_accent_purpose("아, 자고싶다.", "친절하게", "카카오톡")
    # New_Reply_Suggestions_Detailed("아, 자고싶다.", "친절하게", "카카오톡", "자고싶다는 말을 친절하고 차분하게 전달하고싶어요")


    # # test1: 이미지 -> 상황파악
    # image_files = []
    # test_images = ["./AI/OCR_Test1.png", "./AI/OCR_Test2.png", "./AI/OCR_Test3.png", "./AI/OCR_Test4.png"]

    # for image_path in test_images:
    #     try:
    #         with open(image_path, 'rb') as f:
    #             file_content = f.read()
    #             image_files.append((image_path, file_content))
    #     except Exception as e:
    #         logger.error(f"파일 읽기 오류({image_path}): {e}")
    #         continue

    # analyze_situation(image_files)

    # # test2: 이미지 -> 상황파악 + 말투 + 용도
    # Situation_Accent_Purpose(["./AI/OCR_Test1.png","./AI/OCR_Test2.png","./AI/OCR_Test3.png","./AI/OCR_Test4.png"])

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

    # # 로거 설정
    # logger.add("logs/app.log", rotation="500 MB")

    # video_search_service = VideoSearchService()

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
