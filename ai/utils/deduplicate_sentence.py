# 중복되는 문장 제거
def deduplicate_sentences(text: str) -> str:
    """
    문자열에서 중복되는 문장을 제거합니다.
    1. 문자열 전체가 두 번 반복되는 경우
    2. 개별 문장이 반복되는 경우
    """
    if not text:
        return text

    text = text.strip()

    # 1. 전체 문자열이 두 번 반복되는 경우 처리
    half_len = len(text) // 2
    if len(text) % 2 == 0 and text[:half_len] == text[half_len:]:
        return text[:half_len].strip()

    # 2. 개별 문장이 반복되는 경우 처리
    # 마침표, 물음표, 느낌표, 줄바꿈으로 문장 구분
    sentences = []
    current_sentence = ""

    for i, char in enumerate(text):
        current_sentence += char
        # 문장 구분자를 만났거나 마지막 문자인 경우
        if char in [".", "?", "!", "\n"] or i == len(text) - 1:
            current_sentence = current_sentence.strip()
            # 빈 문장이 아니고 중복되지 않은 경우에만 추가
            if current_sentence and current_sentence not in sentences:
                sentences.append(current_sentence)
            current_sentence = ""

    # 결과 조합 시 원래 구분자 유지
    result = ""
    for i, sentence in enumerate(sentences):
        if i > 0:
            # 이전 문장이 줄바꿈으로 끝나지 않았다면 공백 추가
            if not sentences[i - 1].endswith(("\n", ".", "?", "!")):
                result += " "
        result += sentence

    return result
