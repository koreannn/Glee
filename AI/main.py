def get_user_choice():
    print("사진 첨부 OR 사진 미 첨부")
    print("1. 사진 첨부 (OCR 처리)")
    print("2. 사진 첨부하지 않음 (직접 텍스트 입력)")
    choice = input("선택 (1 또는 2): ")
    return choice.strip()


def main():

    choice = get_user_choice()

    if choice == "1":
        # OCR 모듈 임포트 및 실행
        from Img_OCR import run_ocr

        extracted_text = run_ocr()
        # 여기서 추가적으로 LLM 호출 등 후속 처리를 진행할 수 있음.
        print("OCR 결과를 기반으로 답변 생성 로직 진행...")
        # 예시: 답변 생성 함수 호출 (추후 구현)

    elif choice == "2":
        # 사진 없이 직접 텍스트 입력 모듈 임포트 및 실행
        from No_Img import run_no_img

        result = run_no_img()

    # 내용 요약하기 (1. 한줄정도의 매우 짧은 제목 / 2. 두세줄정도의 좀 더 구체적인 요약 내용 (날짜 포함시키기))


if __name__ == "__main__":
    main()
