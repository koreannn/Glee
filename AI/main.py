def get_user_choice():
    print("사진 첨부 OR 사진 미 첨부")
    print("1. 사진 첨부 (OCR 처리)")
    print("2. 사진 첨부하지 않음 (직접 텍스트 입력)")
    choice = input("선택 (1 또는 2): ")
    return choice.strip()


from loguru import logger
from ocr_v2 import (
    analyze_situation_accent_purpose,
    generate_reply_suggestions_detail, analyze_situation,
)

# test1: 이미지 -> 상황파악
# Situation(["./OCR_Test1.png","./OCR_Test2.png","./OCR_Test3.png","./OCR_Test4.png"])

# test2: 이미지 -> 상황파악 + 말투 + 용도
# Situation_Accent_Purpose(["./OCR_Test1.png","./OCR_Test2.png","./OCR_Test3.png","./OCR_Test4.png"])

# # test3: 이미지 -> 답변 추천
# print(Reply_Suggestions(["./OCR_Test1.png","./OCR_Test2.png","./OCR_Test3.png","./OCR_Test4.png"]))

# # test4: 상황+말투+용도 -> 새로운 답변 추천
# situation, accent, purpose = Situation_Accent_Purpose(["./OCR_Test1.png","./OCR_Test2.png","./OCR_Test3.png","./OCR_Test4.png"])
# print(New_Reply_Suggestions(situation, accent, purpose))

# test5: 상황+말투+용도+상세설명 -> 새로운 답변 추천
situation, accent, purpose = analyze_situation_accent_purpose(
    ["./OCR_Test1.png", "./OCR_Test2.png", "./OCR_Test3.png", "./OCR_Test4.png"]
)
logger.info("추가적으로 디테일한 정보 입력:\n")
detail = input()
print(generate_reply_suggestions_detail(situation, accent, purpose, detail))
