def get_user_choice():
    print("사진 첨부 OR 사진 미 첨부")
    print("1. 사진 첨부 (OCR 처리)")
    print("2. 사진 첨부하지 않음 (직접 텍스트 입력)")
    choice = input("선택 (1 또는 2): ")
    return choice.strip()

from loguru import logger
from No_Img import Run_No_Img
from ocr_v2 import CLOVA_OCR, CLOVA_AI_Reply_Summary, CLOVA_AI_Title_Suggestions

choice = get_user_choice()

if choice == "1": # OCR
    OCR_Text = CLOVA_OCR(["./OCR_Test1.png","./OCR_Test2.png","./OCR_Test3.png","./OCR_Test4.png"])
    logger.info("OCR 결과를 기반으로 답변 생성 로직 진행...")
    print("'답장' 1번 OR '이런 느낌으로 작성해주세요' 2번: ")
    choice = input()
    if choice == "1": # 답장 (상황만 요약) -> CLOVA_AI_Reply_Summary
        situation_summary = CLOVA_AI_Reply_Summary(OCR_Text)
        title = CLOVA_AI_Title_Suggestions(OCR_Text) # 제목 생성해보기
        
    # elif choice == "2": # 이런 느낌으로 작성해주세요: 상황, 말투, 용도 세 가지를 리턴해야
        

elif choice == "2": # 사진 없이
    logger.info("No Image")
    result = Run_No_Img()

logger.info("내용 요약 중")



